/**
 * Calculates vault balance with Karma Credit's compounding interest logic.
 * @param {Array} transactions - [{date: 'YYYY-MM-DD', amount: Number}], ordered by date ascending
 * @param {Date} [now] - Optionally set current date for deterministic tests
 * @returns {Number} Final vault balance, rounded to 2 decimals
 */
function calculateVaultBalanceWithInterest(transactions, now = new Date()) {
  if (!transactions || !transactions.length) return 0;

  // Helper: clone date, zero time
  function toDate(d) { let t = new Date(d); t.setHours(0,0,0,0); return t; }

  let txns = transactions
    .map(t => ({ ...t, date: toDate(t.date) }))
    .sort((a, b) => a.date - b.date);

  let current = toDate(txns[0].date);
  let today = toDate(now);

  // Initial values
  let balance = 0;
  let nextPayoutDate = new Date(current);
  nextPayoutDate.setDate(nextPayoutDate.getDate() + 7); // first payout = 1 week after initial deposit

  // Set up "weeks since last reset" for interest ladder
  let weeksSinceReset = 0;
  let lastResetDate = new Date(current);

  // Collect txns into a timeline by date
  let txnIndex = 0;
  let lastWeekBalance = 0;

  // We go week by week, applying interest, handling txns on each week
  while (nextPayoutDate <= today) {
    // Add up all transactions between previous payout and this payout date
    while (
      txnIndex < txns.length &&
      txns[txnIndex].date < nextPayoutDate
    ) {
      let t = txns[txnIndex];
      balance += t.amount;

      // Handle withdrawal >25% of current balance (at time of withdrawal, *before* the withdrawal)
      if (
        t.amount < 0 &&
        (Math.abs(t.amount) > 0.25 * lastWeekBalance)
      ) {
        // Reset ladder, skip payout for this week!
        weeksSinceReset = 0;
        lastResetDate = new Date(t.date);
        // Next payout is 1 week after reset
        nextPayoutDate = new Date(t.date);
        nextPayoutDate.setDate(nextPayoutDate.getDate() + 7);
        // Recompute lastWeekBalance for new ladder
        lastWeekBalance = balance;
        txnIndex++;
        continue; // Don't do payout for this week, skip to next
      }

      txnIndex++;
    }

    // Determine rate for this week of the ladder
    let rate = 0;
    if (weeksSinceReset === 0) rate = 0.0025;
    else if (weeksSinceReset === 1 || weeksSinceReset === 2) rate = 0.005;
    else if (weeksSinceReset === 3 || weeksSinceReset === 4) rate = 0.0075;
    else if (weeksSinceReset >= 5) rate = 0.01;

    // Compound payout based on current balance *before* this week's interest
    let payout = Math.floor(balance * rate);

    balance += payout;

    // For the next week
    lastWeekBalance = balance;
    weeksSinceReset++;
    // Advance to next payout date
    let tmp = new Date(nextPayoutDate);
    tmp.setDate(tmp.getDate() + 7);
    nextPayoutDate = tmp;
  }

  // After last interest payout, apply any remaining transactions up to today
  while (txnIndex < txns.length) {
    balance += txns[txnIndex].amount;
    txnIndex++;
  }

  return Math.floor(balance * 100) / 100;
}
