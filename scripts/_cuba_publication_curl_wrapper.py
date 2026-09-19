#!/usr/bin/env python3
"""Use production curl transport and fast-forward clean Country checkout to latest main."""
import io
import runpy
import subprocess
import urllib.request

# Only a clean, not-yet-staged Country checkout may be rebased to moving main.
subprocess.run(['git', 'diff', '--quiet'], check=True)
subprocess.run(['git', 'diff', '--cached', '--quiet'], check=True)
subprocess.run(['git', 'fetch', '--no-tags', 'origin', '+refs/heads/main:refs/remotes/origin/main'], check=True)
subprocess.run(['git', 'merge-base', '--is-ancestor', 'HEAD', 'origin/main'], check=True)
subprocess.run(['git', 'merge', '--ff-only', 'origin/main'], check=True)
original_urlopen = urllib.request.urlopen

def verified_site_urlopen(request, *args, **kwargs):
    url = request.full_url if isinstance(request, urllib.request.Request) else str(request)
    if url.startswith('https://atlas.yagenji.com/'):
        data = subprocess.check_output(['curl', '-fsSL', '--max-time', '20',
                                        '-H', 'Cache-Control: no-cache',
                                        '-A', 'journey-atlas-production-verifier', url])
        return io.BytesIO(data)
    return original_urlopen(request, *args, **kwargs)

urllib.request.urlopen = verified_site_urlopen
runpy.run_path('../handoff/scripts/_cuba_publication_once.py', run_name='__main__')
