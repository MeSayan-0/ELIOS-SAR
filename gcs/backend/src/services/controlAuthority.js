let authorityEnabled = false;

let enabledAt = null;

export function getControlAuthority() {
  return {
    enabled: authorityEnabled,
    enabledAt,
  };
}

export function enableControlAuthority() {
  authorityEnabled = true;
  enabledAt = new Date();

  return getControlAuthority();
}

export function disableControlAuthority() {
  authorityEnabled = false;
  enabledAt = null;

  return getControlAuthority();
}

export function requireControlAuthority() {
  if (!authorityEnabled) {
    throw new Error(
      "GCS control authority is disabled"
    );
  }
}
