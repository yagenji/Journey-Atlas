#!/usr/bin/env python3
"""Apply an exact display-space target-negative clip to generated map context.

Migration-only Stage 2 safeguard. The approved national SVG paths are never
edited. Their rendered M/L outlines are transformed into user-space coordinates
and used only inside a new clipPath: viewport minus approved target land.

This removes cross-source pale halos and makes every shared land interface
follow the already-approved target silhouette without inventing coastlines or
political boundaries. Existing explicitly reviewed context clips are preserved.
"""
from __future__ import annotations

import math
import re
from xml.etree import ElementTree as ET

SVG = '{http://www.w3.org/2000/svg}'
CLIP_ID = 'map-context-target-negative'

TOKEN = re.compile(r'[MmLlHhVvZz]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')
TRANSFORM = re.compile(r'([A-Za-z]+)\s*\(([^)]*)\)')
NUMBER = re.compile(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')


def _matrix_multiply(left, right):
    """Return affine matrix left ∘ right in SVG (a,b,c,d,e,f) form."""
    a,b,c,d,e,f = left
    A,B,C,D,E,F = right
    return (
        a*A + c*B,
        b*A + d*B,
        a*C + c*D,
        b*C + d*D,
        a*E + c*F + e,
        b*E + d*F + f,
    )


def _parse_transform(value: str):
    result = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    pos = 0
    for match in TRANSFORM.finditer(value.strip()):
        if value[pos:match.start()].strip(' ,\t\r\n'):
            raise ValueError('Unsupported SVG transform syntax')
        name = match.group(1)
        nums = [float(x) for x in NUMBER.findall(match.group(2))]
        if name == 'matrix' and len(nums) == 6:
            current = tuple(nums)
        elif name == 'translate' and len(nums) in (1,2):
            current = (1.0,0.0,0.0,1.0,nums[0],nums[1] if len(nums)==2 else 0.0)
        elif name == 'scale' and len(nums) in (1,2):
            current = (nums[0],0.0,0.0,nums[1] if len(nums)==2 else nums[0],0.0,0.0)
        else:
            raise ValueError(f'Unsupported SVG transform for Stage 2 exact clip: {name}')
        # SVG transform lists apply in written order.
        result = _matrix_multiply(current, result)
        pos = match.end()
    if value[pos:].strip(' ,\t\r\n'):
        raise ValueError('Unsupported trailing SVG transform syntax')
    return result


def _point(matrix, x, y):
    a,b,c,d,e,f = matrix
    return (a*x + c*y + e, b*x + d*y + f)


def _fmt(value):
    if abs(value) < 5e-10:
        value = 0.0
    text = f'{value:.6f}'.rstrip('0').rstrip('.')
    return text or '0'


def _absolute_ml_path(d: str, matrix):
    """Convert M/L/H/V/Z (absolute or relative) to transformed M/L/Z."""
    tokens = TOKEN.findall(d)
    if not tokens:
        raise ValueError('Empty approved target path')
    i = 0
    cmd = None
    x = y = 0.0
    start = None
    out = []

    def is_cmd(token):
        return len(token) == 1 and token.isalpha()

    def number():
        nonlocal i
        if i >= len(tokens) or is_cmd(tokens[i]):
            raise ValueError('Malformed approved target path')
        v = float(tokens[i]); i += 1
        return v

    while i < len(tokens):
        if is_cmd(tokens[i]):
            cmd = tokens[i]; i += 1
            if cmd in 'Zz':
                out.append('Z')
                if start is not None:
                    x,y = start
                cmd = None
                continue
        if cmd is None:
            raise ValueError('Approved target path missing command')

        if cmd in 'Mm':
            rel = cmd == 'm'
            first = True
            while i < len(tokens) and not is_cmd(tokens[i]):
                nx, ny = number(), number()
                if rel:
                    nx, ny = x + nx, y + ny
                x,y = nx,ny
                tx,ty = _point(matrix,x,y)
                out.append(('M' if first else 'L') + ' ' + _fmt(tx) + ',' + _fmt(ty))
                if first:
                    start = (x,y)
                    first = False
            cmd = 'l' if rel else 'L'
        elif cmd in 'Ll':
            rel = cmd == 'l'
            while i < len(tokens) and not is_cmd(tokens[i]):
                nx,ny = number(), number()
                if rel:
                    nx,ny = x+nx,y+ny
                x,y=nx,ny
                tx,ty=_point(matrix,x,y)
                out.append('L '+_fmt(tx)+','+_fmt(ty))
        elif cmd in 'Hh':
            rel = cmd == 'h'
            while i < len(tokens) and not is_cmd(tokens[i]):
                nx=number()
                x = x+nx if rel else nx
                tx,ty=_point(matrix,x,y)
                out.append('L '+_fmt(tx)+','+_fmt(ty))
        elif cmd in 'Vv':
            rel = cmd == 'v'
            while i < len(tokens) and not is_cmd(tokens[i]):
                ny=number()
                y = y+ny if rel else ny
                tx,ty=_point(matrix,x,y)
                out.append('L '+_fmt(tx)+','+_fmt(ty))
        else:
            raise ValueError(f'Unsupported approved target path command: {cmd}')
    return ' '.join(out)


def _effective_fill(node, parents):
    cursor=node
    while cursor is not None:
        if 'style' in cursor.attrib or 'class' in cursor.attrib:
            raise ValueError('Styled approved target requires explicit review')
        if 'fill' in cursor.attrib:
            return cursor.attrib['fill']
        cursor=parents.get(cursor)
    return None


def _target_paths(root):
    parents={child:parent for parent in root.iter() for child in parent}
    targets=[]
    for node in root.iter(SVG+'path'):
        if _effective_fill(node, parents) != 'url(#land)':
            continue
        # Do not treat any non-rendering definitions as approved targets.
        cursor=node
        chain=[]
        while cursor is not None:
            if cursor.tag in (SVG+'defs', SVG+'clipPath', SVG+'mask'):
                raise ValueError('Approved target unexpectedly inside SVG definition')
            if cursor.get('transform'):
                chain.append(_parse_transform(cursor.get('transform')))
            cursor=parents.get(cursor)
        matrix=(1.0,0.0,0.0,1.0,0.0,0.0)
        for transform in chain:  # path first, then each ancestor
            matrix=_matrix_multiply(transform,matrix)
        targets.append((node,matrix))
    if not targets:
        raise ValueError('No approved target paths')
    return targets


def apply_exact_target_negative_clip(svg: str) -> str:
    root=ET.fromstring(svg)
    if root.tag != SVG+'svg' or root.get('viewBox') != '0 0 1200 760':
        raise ValueError('Expected canonical 1200x760 SVG')
    context=root.find(".//*[@id='geographic-context']")
    if context is None:
        return svg
    # Explicit source-reviewed clips remain authoritative.
    if context.get('clip-path'):
        return svg
    if root.find(f".//*[@id='{CLIP_ID}']") is not None:
        raise ValueError('Duplicate exact target-negative clip')

    context_paths=list(context.iter(SVG+'path'))
    if not any((p.get('d') or '').strip() for p in context_paths):
        return svg

    target_data=[]
    for node,matrix in _target_paths(root):
        d=node.get('d','')
        target_data.append(_absolute_ml_path(d,matrix))
    cut='M 0,0 L 1200,0 L 1200,760 L 0,760 Z ' + ' '.join(target_data)
    clip=(f'<clipPath id="{CLIP_ID}" clipPathUnits="userSpaceOnUse">'
          f'<path d="{cut}" fill-rule="evenodd" clip-rule="evenodd"/>'
          '</clipPath>')

    if svg.count('</defs>') != 1:
        raise ValueError('Expected one defs block for exact target-negative clip')
    result=svg.replace('</defs>',clip+'</defs>',1)

    # Replace only the actual rendered geographic-context opening tag.
    match=re.search(r'<g\b(?=[^>]*\bid="geographic-context")[^>]*>',result)
    if not match:
        raise ValueError('Geographic context opening tag missing')
    opening=match.group()
    if 'clip-path=' in opening:
        return result
    updated=opening[:-1] + f' clip-path="url(#{CLIP_ID})">'
    result=result[:match.start()]+updated+result[match.end():]
    ET.fromstring(result)
    return result
