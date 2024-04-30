#!/bin/bash

cuda_version=$(nvidia-smi | grep "CUDA Version" | sed 's/.*CUDA Version: \([0-9]*\.[0-9]*\).*/\1/')
cuda_version_major=$(echo $cuda_version | cut -d. -f1)
cuda_version_minor=$(echo $cuda_version | cut -d. -f2)
cuda_version_number=$((cuda_version_major * 10 + cuda_version_minor))

minimum_cuda_version=120

# Compare the CUDA version
if [ $cuda_version_number -ge $minimum_cuda_version ]; then
    pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
    apt-get install libcublas-12-0
else
    pip install onnxruntime-gpu==1.17.1
fi
