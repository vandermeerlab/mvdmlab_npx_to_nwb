#!/bin/bash

set -eu

generate() {
        # more details might come on https://github.com/ReproNim/neurodocker/issues/330
        [ "$1" == singularity ] && add_entry=' "$@"' || add_entry=''
		ndversion=1.0.1
        docker run --rm repronim/neurodocker:$ndversion \
                generate "$1" \
				--base-image=neurodebian:bookworm \
				--pkg-manager=apt \
				--install build-essential pkg-config git \
				  sudo vim wget strace time ncdu gnupg curl procps pigz less tree visidata \
                --copy environment.yml /opt/environment.yml \
                --miniconda \
                        version=latest \
                        env_name=mvdmlab \
                        env_exists=false \
                        yaml_file=/opt/environment.yml \
                --user=mvdmlab
                # --entrypoint "python3"
				# TODO: may be add dandi and other relevant tools
}

generate docker > Dockerfile
generate singularity > Singularity
