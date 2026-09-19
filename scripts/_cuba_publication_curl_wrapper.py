#!/usr/bin/env python3
"""Use the same curl transport as production verification for live ATLAS GETs."""
import io
import runpy
import subprocess
import urllib.request

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
