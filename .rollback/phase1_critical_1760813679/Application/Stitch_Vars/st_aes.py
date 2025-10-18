# Copyright (c) 2017, Nathan Lopez
# Stitch is under the MIT license. See the LICENSE file at the root of the project for the detailed license terms.

import base64

aes_encoded = 'V3FwbXBaVnViOUhucFBLa1ZDRU4yWjR2blJ0OUQ0U0E='
aes_abbrev = '{}{}{}{}{}{}{}{}{}{}{}{}{}'.format(
    aes_encoded[21],aes_encoded[0],aes_encoded[1],aes_encoded[43],aes_encoded[5],
    aes_encoded[13],aes_encoded[7],aes_encoded[24],aes_encoded[31],
    aes_encoded[35],aes_encoded[16],aes_encoded[39],aes_encoded[28])
secret=base64.b64decode(aes_encoded)