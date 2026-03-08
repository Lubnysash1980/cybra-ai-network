import asyncio
import json
import time
import logging
import os
import hashlib
import aiofiles

logging.basicConfig(level=logging.INFO)

BLOCKCHAIN_FILE = 'blockchain.json'

# Function to hash data using double SHA-256
def hash_data(data):
    if isinstance(data, str):
        data = data.encode()
    elif not isinstance(data, (bytes, bytearray)):
        data = str(data).encode()
    first_hash = hashlib.sha256(data).digest()
    result = hashlib.sha256(first_hash).hexdigest()
    logging.debug(f'Hashed data: {result}')
    return result

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
        logging.info(f'Created block {self.index} with hash {self.hash}')

    def calculate_hash(self):
        payload = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash
        }, sort_keys=True).encode()
        result = hash_data(payload)
        logging.debug(f'Calculated hash for block {self.index}: {result}')
        return result

    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }

    @staticmethod
    def from_dict(d):
        block = Block(d['index'], d['timestamp'], d['data'], d['previous_hash'])
        block.hash = d['hash']
        logging.debug(f'Recreated block from dict: {block.hash}')
        return block

class Blockchain:
    def __init__(self):
        self.chain = []
        self.lock = asyncio.Lock()

    async def initialize(self):
        await self.load_chain()
        logging.info(f'Blockchain initialized with {len(self.chain)} blocks')

    def genesis(self):
        return Block(0, time.time(), {'type': 'genesis'}, '0')

    def latest(self):
        return self.chain[-1] if self.chain else self.genesis()

    async def add_block(self, data):
        async with self.lock:
            block = Block(len(self.chain), time.time(), data, self.latest().hash)
            self.chain.append(block)
            logging.info(f'Added block {block.index} to blockchain')
            if len(self.chain) % 5 == 0:
                await self.save_chain()
            return block

    def validate(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i-1]
            cur = self.chain[i]
            if cur.previous_hash != prev.hash or cur.hash != cur.calculate_hash():
                logging.warning(f'Blockchain invalid at block {cur.index}')
                return False
        logging.info('Blockchain validation passed')
        return True

    async def save_chain(self):
        try:
            async with aiofiles.open(BLOCKCHAIN_FILE, 'w') as f:
                await f.write(json.dumps([b.to_dict() for b in self.chain], indent=4))
            logging.info('Blockchain saved to file')
        except Exception:
            logging.exception('Failed to save blockchain')

    async def load_chain(self):
        if os.path.exists(BLOCKCHAIN_FILE):
            try:
                async with aiofiles.open(BLOCKCHAIN_FILE, 'r') as f:
                    content = await f.read()
                    self.chain = [Block.from_dict(b) for b in json.loads(content)]
                logging.info(f'Loaded blockchain with {len(self.chain)} blocks')
            except Exception:
                logging.exception('Failed to load blockchain, creating genesis')
                self.chain = [self.genesis()]
        else:
            self.chain = [self.genesis()]
            logging.info('No blockchain file found, created genesis block')

# Chat cybraparlament module
class ChatCybraParlament:
    def __init__(self):
        self.messages = []
        self.lock = asyncio.Lock()

    async def add_message(self, sender, content):
        async with self.lock:
            msg = {
                'timestamp': time.time(),
                'sender': sender,
                'content': content
            }
            self.messages.append(msg)
            logging.info(f'New chat message from {sender}: {content}')
            return msg

    async def get_recent_messages(self, limit=10):
        async with self.lock:
            return self.messages[-limit:]

# Example usage
async def main():
    blockchain = Blockchain()
    await blockchain.initialize()
    await blockchain.add_block({'type': 'transaction', 'amount': 100})

    chat = ChatCybraParlament()
    await chat.add_message('Alice', 'Hello Cybra Parliament!')
    recent = await chat.get_recent_messages()
    logging.info(f'Recent messages: {recent}')

if __name__ == '__main__':
    asyncio.run(main())

