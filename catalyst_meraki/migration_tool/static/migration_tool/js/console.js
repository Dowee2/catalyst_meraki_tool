/**
 * Console output polling for background tasks.
 *
 * Polls the task status API endpoint and appends new output lines
 * to the console element in real-time.
 */

function pollTask(taskId, consoleEl, statusEl, actionBtn, resetBtnText, onComplete) {
    const pollUrl = `/api/task/${taskId}/poll/`;
    const interval = 1000; // Poll every second

    function poll() {
        fetch(pollUrl)
            .then(r => r.json())
            .then(data => {
                // Append new output lines
                if (data.output && data.output.length > 0) {
                    data.output.forEach(line => {
                        consoleEl.textContent += line;
                    });
                    // Auto-scroll to bottom
                    consoleEl.scrollTop = consoleEl.scrollHeight;
                }

                if (data.status === 'running') {
                    setTimeout(poll, interval);
                } else if (data.status === 'completed') {
                    statusEl.textContent = 'Completed successfully!';
                    statusEl.className = 'status-text status-success';
                    actionBtn.disabled = false;
                    actionBtn.textContent = resetBtnText;
                    if (onComplete) {
                        onComplete(data);
                    }
                } else if (data.status === 'error') {
                    statusEl.textContent = 'Task failed: ' + (data.error || 'Unknown error');
                    statusEl.className = 'status-text status-error';
                    actionBtn.disabled = false;
                    actionBtn.textContent = resetBtnText;
                }
            })
            .catch(err => {
                statusEl.textContent = 'Polling error: ' + err;
                statusEl.className = 'status-text status-error';
                actionBtn.disabled = false;
                actionBtn.textContent = resetBtnText;
            });
    }

    poll();
}
