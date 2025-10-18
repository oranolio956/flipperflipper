# How to Stop a Frozen Cursor Agent in Web Browser

When the Cursor AI agent is stuck spinning and not responding in the web browser version, here are several methods to stop it:

## Quick Solutions (Try These First)

### 1. **ESC Key** (Primary Method)
- Press the `ESC` key on your keyboard
- This is the standard way to cancel/stop a running Cursor agent operation
- May need to press it multiple times if the agent is deeply stuck

### 2. **Stop Button in UI**
- Look for a "Stop" or "Cancel" button that appears near the spinning indicator
- Usually appears as a square stop icon (■) or "Stop generating" button
- Click it to halt the current operation

### 3. **Keyboard Shortcuts**
- **Ctrl+C** (Windows/Linux) or **Cmd+C** (Mac) - Sometimes works to interrupt
- **Ctrl+Shift+P** / **Cmd+Shift+P** - Open command palette and look for "Stop" or "Cancel" commands

## If Quick Solutions Don't Work

### 4. **Refresh the Page**
- **Ctrl+R** (Windows/Linux) or **Cmd+R** (Mac)
- This will reload the Cursor web interface
- Note: You may lose unsaved work in the current session

### 5. **Close and Reopen the Tab**
- Close the browser tab completely
- Open a new tab and navigate back to Cursor
- This gives you a fresh session

### 6. **Hard Refresh** (Clears Cache)
- **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac)
- This clears cached data and fully reloads the page
- Useful if the issue is related to cached state

### 7. **Browser Developer Console**
- Open Developer Tools: **F12** or **Ctrl+Shift+I** (Windows/Linux) / **Cmd+Option+I** (Mac)
- Go to the Console tab
- Type: `location.reload()` and press Enter
- Or look for any error messages that might indicate the problem

## Prevention Tips

### To Avoid Future Freezes:
1. **Break down large requests** into smaller, more manageable tasks
2. **Be specific** in your prompts to avoid the agent getting stuck in loops
3. **Save your work frequently** using Ctrl+S / Cmd+S
4. **Monitor memory usage** - Close unnecessary browser tabs if memory is high
5. **Use a stable internet connection** - Connection issues can cause the agent to hang
6. **Keep your browser updated** to the latest version

## Browser-Specific Tips

### Chrome/Edge
- Task Manager: **Shift+ESC** to see which tabs are using resources
- Can kill specific processes if needed

### Firefox
- about:performance in address bar to check tab performance
- Can reload specific tabs from there

### Safari
- Develop menu > Show Web Inspector for debugging
- Activity Monitor to check browser resource usage

## When Nothing Else Works

If the agent remains completely frozen:
1. **Save any important work** in other tabs/applications
2. **Screenshot error messages** if visible
3. **Close the entire browser** (not just the tab)
4. **Restart your browser** and try again
5. **Clear browser data** if the issue persists:
   - Settings → Privacy → Clear browsing data
   - Select "Cached images and files" and "Cookies and other site data"

## Reporting the Issue

If you encounter frequent freezing:
- Note the exact steps that led to the freeze
- Check browser console for error messages (F12 → Console)
- Report to Cursor support with:
  - Browser version
  - Operating system
  - What you were doing when it froze
  - Any error messages
  - Screenshots if possible

## Emergency Workspace Recovery

If you lose work due to a freeze:
- Cursor often auto-saves your work
- Check the file system for recent changes
- Look for backup or recovery options in Cursor settings
- Use browser history to recover recently closed tabs

Remember: The **ESC key** is your first line of defense and works in most cases!