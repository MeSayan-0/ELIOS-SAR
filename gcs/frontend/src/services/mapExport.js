export function downloadMapJson(mapData) {
  if (!mapData) {
    throw new Error("No map data available");
  }

  const blob = new Blob(
    [
      JSON.stringify(
        mapData,
        null,
        2
      ),
    ],
    {
      type: "application/json",
    }
  );

  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;

  link.download =
    `${mapData.mapId || "elios-sar-map"}.json`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  URL.revokeObjectURL(url);
}
