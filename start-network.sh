podman run --privileged -it -v ./topo:/topo:z -v ./tmp:/tmp --pod onos --entrypoint /topo/entrypoint.sh opennetworking/mn-stratum
