export function configureSocket(io) {
  io.on("connection", (socket) => {
    console.log(
      `GCS client connected: ${socket.id}`
    );

    socket.on("disconnect", () => {
      console.log(
        `GCS client disconnected: ${socket.id}`
      );
    });
  });
}

export function broadcastState(io, state) {
  io.emit("gcs:state", state);
}
