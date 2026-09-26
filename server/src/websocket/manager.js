const clients = new Set();

export function addClient(ws) {
  clients.add(ws);
}

export function removeClient(ws) {
  clients.delete(ws);
}

export function broadcast(message) {
  const encoded = JSON.stringify(message);

  for (const client of clients) {
    if (client.readyState === 1) {
      client.send(encoded);
    }
  }
}

export function getClientCount() {
  return clients.size;
}
