
class FixedProtocol:
    """Fixed AES-encrypted protocol for Stitch"""
    
    def __init__(self):
        self.key = None
        self.cipher = None
        
    def generate_key(self):
        """Generate random AES key"""
        self.key = get_random_bytes(32)  # AES-256
        return base64.b64encode(self.key).decode()
        
    def set_key(self, key_b64):
        """Set AES key from base64"""
        self.key = base64.b64decode(key_b64)
        
    def encrypt(self, data):
        """Encrypt data with AES"""
        if not self.key:
            raise ValueError("No encryption key set")
            
        # Create new cipher for each message
        iv = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # Pad and encrypt
        padded = pad(data.encode() if isinstance(data, str) else data, AES.block_size)
        encrypted = cipher.encrypt(padded)
        
        # Return IV + encrypted data
        return base64.b64encode(iv + encrypted).decode()
        
    def decrypt(self, data_b64):
        """Decrypt AES data"""
        if not self.key:
            raise ValueError("No encryption key set")
            
        # Decode from base64
        data = base64.b64decode(data_b64)
        
        # Extract IV and ciphertext
        iv = data[:16]
        ciphertext = data[16:]
        
        # Decrypt
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        
        # Unpad
        unpadded = unpad(decrypted, AES.block_size)
        
        return unpadded.decode()
        
    def handshake_server(self, conn):
        """Server-side handshake"""
        try:
            # Receive client hello
            hello = conn.recv(1024).strip()
            
            if hello != b'STITCH_HELLO':
                return False, "Invalid hello"
                
            # Generate and send key
            key_b64 = self.generate_key()
            conn.send(f"KEY:{key_b64}\n".encode())
            
            # Receive encrypted confirmation
            encrypted_confirm = conn.recv(1024).strip().decode()
            
            # Decrypt and verify
            confirm = self.decrypt(encrypted_confirm)
            
            if confirm == "CONFIRMED":
                conn.send(b"READY\n")
                return True, "Handshake successful"
            else:
                return False, "Invalid confirmation"
                
        except Exception as e:
            return False, f"Handshake error: {e}"
            
    def handshake_client(self, sock):
        """Client-side handshake"""
        try:
            # Send hello
            sock.send(b'STITCH_HELLO\n')
            
            # Receive key
            response = sock.recv(1024).strip().decode()
            
            if not response.startswith('KEY:'):
                return False, "No key received"
                
            key_b64 = response[4:]
            self.set_key(key_b64)
            
            # Send encrypted confirmation
            encrypted = self.encrypt("CONFIRMED")
            sock.send(f"{encrypted}\n".encode())
            
            # Wait for ready
            ready = sock.recv(1024).strip()
            
            if ready == b'READY':
                return True, "Handshake successful"
            else:
                return False, "Server not ready"
                
        except Exception as e:
            return False, f"Handshake error: {e}"
