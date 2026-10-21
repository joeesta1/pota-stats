/**
 * W4WJE POTA spot history -> Google Drive (runs in the w4wje73@gmail.com Google account)
 *
 * Pulls every activation archived by the w4wje-live Cloudflare Worker and keeps, in Drive:
 *   - folder "W4WJE POTA Spot History" with one CSV + one JSON file per activation
 *   - Google Sheet "W4WJE POTA Spots" inside that folder:
 *       "Activations" tab = one row per activation, "Spots" tab = every spot of every activation
 *
 * Setup (once): paste this file into a new Apps Script project, run setup(), approve access.
 * After that a time trigger runs syncSpots() every hour. Only new/changed activations are re-copied.
 */
const WORKER = "https://w4wje-live.joe-estabrooks.workers.dev";
const FOLDER_NAME = "W4WJE POTA Spot History";
const SHEET_NAME = "W4WJE POTA Spots";

function setup() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === "syncSpots")
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("syncSpots").timeBased().everyHours(1).create();
  syncSpots();
}

function syncSpots() {
  const props = PropertiesService.getScriptProperties();
  const folder = getFolder_();
  const ss = getSpreadsheet_(folder);
  const idx = JSON.parse(UrlFetchApp.fetch(WORKER + "/archive").getContentText());
  const acts = idx.activations || [];
  let changed = 0;

  for (const a of acts) {
    const sig = a.last + "|" + a.spots;
    if (props.getProperty("act:" + a.id) === sig) continue;
    const csv = UrlFetchApp.fetch(WORKER + "/archive/" + a.id + ".csv").getContentText();
    const json = UrlFetchApp.fetch(WORKER + "/archive/" + a.id + ".json").getContentText();
    putFile_(folder, "W4WJE_" + a.id + ".csv", csv, "text/csv");
    putFile_(folder, "W4WJE_" + a.id + ".json", json, "application/json");
    replaceSpots_(ss, a.id, Utilities.parseCsv(csv.replace(/\r\n/g, "\n").trim()));
    props.setProperty("act:" + a.id, sig);
    changed++;
  }

  writeActivations_(ss, acts);
  console.log("Activations: " + acts.length + ", updated: " + changed);
}

function getFolder_() {
  const it = DriveApp.getFoldersByName(FOLDER_NAME);
  return it.hasNext() ? it.next() : DriveApp.createFolder(FOLDER_NAME);
}

function getSpreadsheet_(folder) {
  const it = folder.getFilesByName(SHEET_NAME);
  if (it.hasNext()) return SpreadsheetApp.open(it.next());
  const ss = SpreadsheetApp.create(SHEET_NAME);
  DriveApp.getFileById(ss.getId()).moveTo(folder);
  ss.getSheets()[0].setName("Activations");
  ss.insertSheet("Spots");
  return ss;
}

function putFile_(folder, name, content, mime) {
  const it = folder.getFilesByName(name);
  if (it.hasNext()) it.next().setContent(content);
  else folder.createFile(name, content, mime);
}

// Replace all rows of one activation in the Spots tab (keeps the tab sorted by activation/time).
function replaceSpots_(ss, id, rows) {
  const sh = ss.getSheetByName("Spots") || ss.insertSheet("Spots");
  const header = rows[0];
  const fresh = rows.slice(1).filter(r => r.length === header.length);
  const n = sh.getLastRow();
  let data = n > 1 ? sh.getRange(2, 1, n - 1, header.length).getValues() : [];
  data = data.filter(r => String(r[0]) !== id).concat(fresh);
  data.sort((x, y) => String(x[3]).localeCompare(String(y[3])));
  sh.clearContents();
  sh.getRange(1, 1, 1, header.length).setValues([header]).setFontWeight("bold");
  if (data.length) sh.getRange(2, 1, data.length, header.length).setNumberFormat("@").setValues(data);
  sh.setFrozenRows(1);
}

function writeActivations_(ss, acts) {
  const sh = ss.getSheetByName("Activations") || ss.insertSheet("Activations");
  const header = ["activation_id", "park", "park_name", "start_utc", "last_spot_utc", "spots", "status", "csv_url"];
  const rows = acts.map(a => [a.id, a.ref, a.name, a.start, a.last, a.spots,
    a.current ? "current / most recent" : "archived", WORKER + "/archive/" + a.id + ".csv"]);
  sh.clearContents();
  sh.getRange(1, 1, 1, header.length).setValues([header]).setFontWeight("bold");
  if (rows.length) sh.getRange(2, 1, rows.length, header.length).setValues(rows);
  sh.setFrozenRows(1);
}
