import os
import sys
import subprocess

def run(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        return out.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.output.strip()}"
    except FileNotFoundError:
        return "NOT FOUND"

print('=== System GPU / Driver / CUDA check ===')
print('\n-- nvidia-smi --')
print(run('nvidia-smi'))

print('\n-- nvcc --version (if nvcc in PATH) --')
print(run('nvcc --version'))

print('\n-- CUDA toolkit directories (default) --')
cuda_root = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA'
if os.path.isdir(cuda_root):
    try:
        versions = [d for d in os.listdir(cuda_root) if os.path.isdir(os.path.join(cuda_root, d))]
        print('Found CUDA toolkit folders:', versions)
    except Exception as e:
        print('ERROR listing CUDA folders:', e)
else:
    print('Default CUDA path not found:', cuda_root)

print('\n-- Searching for cuDNN DLLs in CUDA folders (first 10 matches) --')
found = []
if os.path.isdir(cuda_root):
    for root, dirs, files in os.walk(cuda_root):
        for fname in files:
            if 'cudnn' in fname.lower():
                found.append(os.path.join(root, fname))
                if len(found) >= 10:
                    break
        if len(found) >= 10:
            break
print('\n'.join(found) if found else 'No cuDNN DLLs found in default CUDA path')

print('\n=== Python / Virtualenv checks ===')
print('Python executable:', sys.executable)

# Try to import torch
try:
    import importlib, json
    torch = importlib.import_module('torch')
    print('\n-- torch --')
    try:
        print('torch.__version__ =', torch.__version__)
    except Exception:
        pass
    try:
        print('torch.version.cuda =', getattr(torch, 'version', None) and getattr(torch.version, 'cuda', None))
    except Exception:
        pass
    try:
        print('torch.cuda.is_available() =', torch.cuda.is_available())
    except Exception as e:
        print('Error checking torch.cuda.is_available():', e)
except Exception as e:
    print('\nTorch not installed or import error:', e)

# Try to import tensorflow
try:
    import importlib
    tf = importlib.import_module('tensorflow')
    print('\n-- tensorflow --')
    try:
        print('tensorflow.__version__ =', tf.__version__)
    except Exception:
        pass
    try:
        gpus = tf.config.list_physical_devices('GPU')
        print('tensorflow GPUs detected =', gpus)
    except Exception as e:
        print('Error listing TF GPUs:', e)
except Exception as e:
    print('\nTensorFlow not installed or import error:', e)

print('\n-- pip show nvidia-ml-py3 (optional NVIDIA python bindings) --')
print(run('python -m pip show nvidia-ml-py3'))

print('\nDiagnostic complete.')
