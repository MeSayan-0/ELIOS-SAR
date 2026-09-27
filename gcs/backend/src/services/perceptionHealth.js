import { getStreamHealth } from "./streamHealthService.js";
import { getSynchronizationState } from "./frameSynchronizer.js";

export function getPerceptionHealth() {
  return {
    timestamp: new Date().toISOString(),
    streams: getStreamHealth(),
    synchronization: getSynchronizationState()
  };
}
