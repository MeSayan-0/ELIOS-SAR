import express from "express";
import { getStateSnapshot } from "../services/gcsState.js";

const router = express.Router();

router.get("/", (req, res) => {
  res.json(getStateSnapshot());
});

export default router;
