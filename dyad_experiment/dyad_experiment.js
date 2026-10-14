// Minimal dyad experiment script
const MAX_TRIALS = 150;
const START_TOKENS = 10;

let trial = 0;
let tokens = [START_TOKENS, START_TOKENS];
let choices = [null, null];
let logRows = [];

// Elements
const trialDisplay = document.getElementById('trialDisplay');
const maxTrialsDisplay = document.getElementById('maxTrials');
const p1tokensEl = document.getElementById('p1tokens');
const p2tokensEl = document.getElementById('p2tokens');
const p1choiceEl = document.getElementById('p1choice');
const p2choiceEl = document.getElementById('p2choice');
const logEl = document.getElementById('log');
const startBtn = document.getElementById('startBtn');
const downloadBtn = document.getElementById('downloadBtn');

const p1red = document.getElementById('p1red');
const p1black = document.getElementById('p1black');
const p2red = document.getElementById('p2red');
const p2black = document.getElementById('p2black');

maxTrialsDisplay.textContent = MAX_TRIALS;

startBtn.addEventListener('click', startExperiment);
downloadBtn.addEventListener('click', downloadCSV);

p1red.addEventListener('click', () => handleChoice(1, 'Red'));
p1black.addEventListener('click', () => handleChoice(1, 'Black'));
p2red.addEventListener('click', () => handleChoice(2, 'Red'));
p2black.addEventListener('click', () => handleChoice(2, 'Black'));

function startExperiment(){
  trial = 0;
  tokens = [START_TOKENS, START_TOKENS];
  choices = [null, null];
  logRows = [];
  logEl.value = '';
  updateDisplays();
  startBtn.disabled = true;
  downloadBtn.disabled = true;
  startTrial();
}

function startTrial(){
  if (isFinished()) return endExperiment();
  trial += 1;
  choices = [null, null];
  p1choiceEl.textContent = '—';
  p2choiceEl.textContent = '—';
  setButtonsDisabled(false);
  updateDisplays();
}

function handleChoice(player, choice){
  // player: 1 or 2
  choices[player-1] = choice;
  if (player === 1) p1choiceEl.textContent = choice;
  else p2choiceEl.textContent = choice;
  // disable that player's buttons until next trial
  if (player === 1) { p1red.disabled = true; p1black.disabled = true; }
  else { p2red.disabled = true; p2black.disabled = true; }

  if (choices[0] && choices[1]) {
    // Both chosen -> resolve
    setTimeout(resolveTrial, 200);
  }
}

function resolveTrial(){
  let result = 'tie';
  if (choices[0] === choices[1]) {
    // tie, no tokens change
    result = 'tie';
  } else {
    // different choices -> randomly pick a winner (zero-sum)
    const winner = Math.random() < 0.5 ? 1 : 2;
    result = `player${winner}_wins`;
    if (winner === 1) { tokens[0] += 1; tokens[1] -= 1; }
    else { tokens[1] += 1; tokens[0] -= 1; }
  }

  // Log
  const row = {
    trial: trial,
    p1choice: choices[0],
    p2choice: choices[1],
    p1tokens: tokens[0],
    p2tokens: tokens[1],
    result: result,
    timestamp: new Date().toISOString()
  };
  logRows.push(row);
  appendLog(row);
  updateDisplays();
  setButtonsDisabled(true);

  if (isFinished()) return endExperiment();

  // Continue to next trial after short delay
  setTimeout(startTrial, 500);
}

function isFinished(){
  if (trial >= MAX_TRIALS) return true;
  if (tokens[0] <= 0 || tokens[1] <= 0) return true;
  return false;
}

function endExperiment(){
  setButtonsDisabled(true);
  startBtn.disabled = false;
  downloadBtn.disabled = false;
  let msg = `Experiment finished after ${trial} trials. `;
  if (tokens[0] <= 0) msg += 'Player 1 ran out of tokens.';
  else if (tokens[1] <= 0) msg += 'Player 2 ran out of tokens.';
  else msg += 'Max trials reached.';
  appendLog({trial: trial, p1choice: '', p2choice: '', p1tokens: tokens[0], p2tokens: tokens[1], result: msg, timestamp: new Date().toISOString()});
}

function updateDisplays(){
  trialDisplay.textContent = trial;
  p1tokensEl.textContent = tokens[0];
  p2tokensEl.textContent = tokens[1];
}

function setButtonsDisabled(disabled){
  p1red.disabled = disabled;
  p1black.disabled = disabled;
  p2red.disabled = disabled;
  p2black.disabled = disabled;
  // If enabling, ensure per-player buttons are enabled (not both waiting)
  if (!disabled){
    p1red.disabled = false; p1black.disabled = false;
    p2red.disabled = false; p2black.disabled = false;
  }
}

function appendLog(row){
  const line = `${row.trial},${row.p1choice || ''},${row.p2choice || ''},${row.p1tokens},${row.p2tokens},${row.result},${row.timestamp}`;
  logEl.value += line + '\n';
  logEl.scrollTop = logEl.scrollHeight;
}

function downloadCSV(){
  let csv = 'trial,p1choice,p2choice,p1tokens,p2tokens,result,timestamp\n';
  for (const r of logRows){
    csv += `${r.trial},${r.p1choice || ''},${r.p2choice || ''},${r.p1tokens},${r.p2tokens},${r.result},${r.timestamp}\n`;
  }
  // final summary row
  csv += `final, , ,${tokens[0]},${tokens[1]},summary,${new Date().toISOString()}\n`;
  const blob = new Blob([csv], {type: 'text/csv'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `dyad_experiment_log_${new Date().toISOString().replace(/[:.]/g,'-')}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
