import { Ros, Topic } from "roslib";

const ROSBRIDGE_URL =
  process.env.ROSBRIDGE_URL ||
  "ws://127.0.0.1:9090";

const DRONE_COMMAND_TOPIC =
  process.env.DRONE_COMMAND_TOPIC ||
  "/gcs/drone/command";

const ROVER_CMD_VEL_TOPIC =
  process.env.ROVER_CMD_VEL_TOPIC ||
  "/rover/cmd_vel";

let ros = null;
let commandTopic = null;
let roverCommandTopic = null;
let reconnectTimer = null;

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    startRosCommandGateway();
  }, 2000);
}

export function startRosCommandGateway() {
  if (ros && ros.isConnected) {
    return ros;
  }

  try {
    ros = new Ros({
      url: ROSBRIDGE_URL,
    });

    ros.on("connection", () => {
      console.log("[ROS] Command gateway connected");
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      commandTopic = new Topic({
        ros,
        name: DRONE_COMMAND_TOPIC,
        messageType: "std_msgs/String",
      });

      roverCommandTopic = new Topic({
        ros,
        name: ROVER_CMD_VEL_TOPIC,
        messageType: "geometry_msgs/Twist",
      });
    });

    ros.on("error", (error) => {
      console.warn(
        "[ROS] Command gateway connection warning:",
        error?.message || error
      );
      commandTopic = null;
      roverCommandTopic = null;
      if (ros) {
        try {
          ros.close();
        } catch (_) {}
        ros = null;
      }
      scheduleReconnect();
    });

    ros.on("close", () => {
      console.log("[ROS] Command gateway disconnected; scheduling reconnect...");
      commandTopic = null;
      roverCommandTopic = null;
      ros = null;
      scheduleReconnect();
    });
  } catch (err) {
    console.warn("[ROS] Could not initialize Ros:", err?.message || err);
    scheduleReconnect();
  }

  return ros;
}

function getDroneCommandTopic() {
  if (commandTopic && ros && ros.isConnected) {
    return commandTopic;
  }

  startRosCommandGateway();

  if (!commandTopic && ros) {
    commandTopic = new Topic({
      ros,
      name: DRONE_COMMAND_TOPIC,
      messageType: "std_msgs/String",
    });
  }

  return commandTopic;
}

function getRoverCommandTopic() {
  if (roverCommandTopic && ros && ros.isConnected) {
    return roverCommandTopic;
  }

  startRosCommandGateway();

  if (!roverCommandTopic && ros) {
    roverCommandTopic = new Topic({
      ros,
      name: ROVER_CMD_VEL_TOPIC,
      messageType: "geometry_msgs/Twist",
    });
  }

  return roverCommandTopic;
}

export function publishRoverCommand({
  vehicleId,
  command,
  commandId,
  metadata = {},
}) {
  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  if (!command) {
    throw new Error("command is required");
  }

  const plainCommand = String(command).trim().toUpperCase();

  const speed =
    metadata?.speed === undefined
      ? 0.5
      : Number(metadata.speed);

  if (!Number.isFinite(speed) || speed < 0) {
    throw new Error("Rover speed must be a non-negative number");
  }

  const message = {
    linear: {
      x: 0,
      y: 0,
      z: 0,
    },
    angular: {
      x: 0,
      y: 0,
      z: 0,
    },
  };

  switch (plainCommand) {
    case "FORWARD":
      message.linear.x = speed;
      break;

    case "BACK":
      message.linear.x = -speed;
      break;

    case "LEFT":
      message.angular.z = speed;
      break;

    case "RIGHT":
      message.angular.z = -speed;
      break;

    case "STOP":
    case "DOCK":
    case "RETURN_TO_DOCK":
    case "ABORT":
      break;

    default:
      throw new Error(
        `Unsupported rover motion command: ${plainCommand}`
      );
  }

  const topic = getRoverCommandTopic();

  if (!topic) {
    throw new Error("Rover ROS command topic is not available");
  }

  topic.publish(message);

  return true;
}

export function publishDroneCommand({
  vehicleId,
  command,
  commandId,
}) {
  if (!vehicleId) {
    throw new Error(
      "vehicleId is required"
    );
  }

  if (!command) {
    throw new Error(
      "command is required"
    );
  }

  const topic = getDroneCommandTopic();

  const plainCommand = String(command).trim().toUpperCase();

  topic.publish({
    data: plainCommand,
  });

  return true;
}

export function isRosCommandConnected() {
  return Boolean(ros && ros.isConnected);
}

