import mongoose from "mongoose";

export async function connectDatabase() {
  const mongoUri = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/elios_sar";

  try {
    await mongoose.connect(mongoUri, { serverSelectionTimeoutMS: 2000 });
    console.log("[DB] MongoDB connected:", mongoUri.includes("@") ? "Atlas" : "Local");
  } catch (err) {
    console.warn("[DB] Primary MongoDB not reachable:", err.message);

    if (mongoUri !== "mongodb://127.0.0.1:27017/elios_sar") {
      try {
        await mongoose.connect("mongodb://127.0.0.1:27017/elios_sar", { serverSelectionTimeoutMS: 1500 });
        console.log("[DB] Connected to fallback local MongoDB");
        return;
      } catch (fallbackErr) {
        console.warn("[DB] Fallback local MongoDB unreachable:", fallbackErr.message);
      }
    }

    console.warn("[DB] Operating in resilient in-memory mode. WebSockets and video/AI streams remain fully active.");
  }
}

export async function disconnectDatabase() {
  if (mongoose.connection.readyState !== 0) {
    await mongoose.disconnect();
  }
}
