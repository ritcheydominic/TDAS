# TDAS
 Utilities for Timestamped Document Authenticity Seal (TDAS) research project

## timestamp-utils.py
### Prerequisites

- OpenTimestamps Client: The client is necessary for both creating and verifying timestamps.

    - Install via PyPi:
    ```
    pip3 install opentimestamps-client
    ```
    - Or, if you prefer, install from source:
    ```
    python3 setup.py install
    ```

- Bitcoin Core Node: Required only for verification. A pruned node is sufficient.

### Setting Up Bitcoin Core Node
This is needed to use the verify method. 
1. Download Bitcoin Core from the official site.
2. Configure your bitcoin core with the following settings in bitcoin.conf. You can prune if you like. 
    ```
    server=1
    rpcuser=YOUR_USERNAME
    rpcpassword=YOUR_PASS
    ```
3. Use the following command to start up the node. 
    ```
    bitcoind -daemon
    ```
4. Use the command to following command to stop the node. 
    ```
    bitcoin-cli stop
    ```
### Timestamping 
- The timestamp_signature function saves a signature to a file and creates a timestamp proof using the OpenTimestamps protocol. Please note, when you stamp it takes a few hours for the timestamp to get confirmed by the Bitcoin blockchain. 
Example usage: 
    ```
    signature = "example signature content"
    output_path = "path/to/output/file.ots"
    ots_file = timestamp_signature(signature, output_path)
    ```

- The verify_timestamp function verifies the timestamp of a signature file. You need a local Bitcoin Core node (a pruned node is fine).
Example usage: 
    ```
    ots_file_path = "path/to/timestamped/file.ots"
    verification_result = verify_timestamp(ots_file_path)
    ```
For more advanced configurations or troubleshooting, please see the [OpenTimestamps documentation](https://github.com/opentimestamps/opentimestamps-client).