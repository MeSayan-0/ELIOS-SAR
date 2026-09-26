import mongoose from "mongoose";

export async function connectDatabase() {
  const mongoUri = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/elios_sar";

  try {
    await mongoose.connect(mongoUri, { serverSelectionTimeoutMS: 2500 });
    console.log("MongoDB connected:", mongoUri.includes("@") ? "Atlas" : "Local");
  } catch (err) {
    console.warn("Could not connect to primary MongoDB, attempting local fallback:", err.message);
    await mongoose.connect("mongodb://127.0.0.1:27017/elios_sar");
    console.log("Connected to fallback local MongoDB");
  }
}

export async function disconnectDatabase() {
  await mongoose.disconnect();
}
