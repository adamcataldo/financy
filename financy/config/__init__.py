import os
import warnings

if 'LOCAL_FINANCY' not in os.environ:
    warnings.warn('No environment variable found named $LOCAL_FINANCY. Using $HOME instead')
    local_financy = os.environ['HOME']
else:
    local_financy = os.environ['LOCAL_FINANCY']

fmp_api_calls_per_minute = 300
with open(f"{local_financy}/.apikey") as f:
    fmp_apikey = f.read().strip()

reports_dir = f"{local_financy}/reports"
