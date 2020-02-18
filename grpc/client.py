#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys


import grpc
import data_pb2
import data_pb2_grpc


host = sys.argv[1]

# _HOST = 'localhost'
_HOST = host
_PORT = '8888'

def run():
    with open('server.crt', 'rb') as f:
        trusted_certs = f.read()

    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
    conn = grpc.secure_channel(_HOST + ':' + _PORT, credentials)

    # conn = grpc.insecure_channel(_HOST + ':' + _PORT)
    client = data_pb2_grpc.FormatDataStub(channel=conn)
    response = client.DoFormat(data_pb2.Data(text='hello,world!'))
    print("received: " + response.text)

if __name__ == '__main__':
    run()


