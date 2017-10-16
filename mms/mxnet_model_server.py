# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#     http://www.apache.org/licenses/LICENSE-2.0
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

from arg_parser import ArgParser
from log import get_logger
from serving_frontend import ServingFrontend
from client_sdk_generator import ClientSDKGenerator


logger = get_logger(__name__)


class MMS(object):
    '''MXNet Model Serving
    '''
    def __init__(self, app_name='mms'):
        # Initialize serving frontend and arg parser
        try:
            self.args = ArgParser.parse_args()
            self.serving_frontend = ServingFrontend(app_name)

            logger.info('Initialized model serving.')
        except Exception as e:
            logger.error('Failed to initialize model serving: ' + str(e))
            exit(1)
        
    def start_model_serving(self):
        '''Start model serving server
        '''
        try:
            # Port 
            self.port = self.args.port or 8080
            self.host = self.args.host or '127.0.0.1'

            # Register user defined model service or default mxnet_vision_service
            class_defs = self.serving_frontend.register_module(self.args.service)
            if len(class_defs) < 2:
                raise Exception('User defined module must derive base ModelService.')
            # First class is the base ModelService class
            mode_class_name = class_defs[1].__name__

            # Load models using registered model definitions
            registered_models = self.serving_frontend.get_registered_modelservices()
            ModelClassDef = registered_models[mode_class_name]
            self.serving_frontend.load_models(self.args.models, ModelClassDef)
            if len(self.args.models) > 5:
                raise Exception('Model number exceeds our system limits: 5')

            # Setup endpoint
            openapi_endpoints = self.serving_frontend.setup_openapi_endpoints(self.host, self.port)

            # Generate client SDK
            if self.args.gen_api is not None:
                ClientSDKGenerator.generate(openapi_endpoints, self.args.gen_api)

            # Start model serving host
            self.serving_frontend.start_handler(self.host, self.port)

            logger.info('Host is started at ' + self.host + ':' + str(self.port))

        except Exception as e:
            logger.error('Failed to start model serving host: ' + str(e))
            exit(1)
        

def start_serving():
    mms = MMS()
    mms.start_model_serving()

if __name__ == '__main__':
    start_serving()