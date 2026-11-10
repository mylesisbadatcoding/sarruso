# Offline Voice Note Capture App
 
## Prompt for Claude
 
I want help designing and building a small, offline voice-note capture app. It should do one job well: capture spoken notes, turn them into clean text, and export them to my main note-taking system. It should not try to be a full note-taking app.
 
Context: I often take notes while driving, so the app needs to work with no internet connection and be quick to use hands-free.
 
Requirements:
- Voice recognition runs fully on-device.
- A small local language model (small enough to download to a phone or laptop, target roughly 8 GB or less, to be confirmed) handles basic voice commands such as "create a new note," "put this in quotation marks," and "new paragraph."
- Recording, transcription, and command handling all work offline.
- Notes do not persist inside the app. When I finish, the app exports the text to my main system.
- The app should be simple: record, review, export.
Please help me with:
1. Choosing an on-device speech-to-text model and a small local LLM that fit the size and speed limits.
2. Picking a platform and stack (for example, a mobile app or a desktop app) that is realistic for a solo builder.
3. Designing the command set and how the model maps spoken commands to text actions.
4. Defining the export format and how notes get sent to my main system.
5. A step-by-step build plan, starting with a minimal prototype.
Start by asking me any questions that would change the design, then propose an approach.
 
## Summary of Needs and Wants
 
**Needs**
- Works fully offline.
- On-device voice recognition.
- Small on-device language model for basic commands.
- Records and transcribes notes quickly.
- Exports notes to my main note-taking system.
- Does not store notes long-term inside the app.
**Wants**
- Hands-free use while driving.
- Basic formatting commands (quotes, new paragraph, new note).
- Simple, one-purpose interface with no extra features.
**Inspiration:** Wispr Flow, which turns voice into text wherever you need it without building a whole note app.
 
**Open question:** The "8-byte" figure in my notes is probably "8 GB." Confirm the size target before choosing models.
 
## Project Steps
 
1. **Define the target size and platform.** Decide the maximum model download size and whether the app is for phone, laptop, or both.
2. **Research on-device speech-to-text.** Compare small offline models for accuracy, speed, and size.
3. **Research small local language models.** Find one that can reliably map short spoken commands to actions within the size limit.
4. **Define the command set.** List the first 5 to 10 commands (create note, new paragraph, quote, undo, export, and so on).
5. **Define the export path.** Choose the destination (file drop, share sheet, clipboard, or API) and the output format (plain text or markdown).
6. **Build a minimal prototype.** Record, transcribe, and export one note offline.
7. **Add the command layer.** Connect the local model to the command set.
8. **Test while driving.** Check that the flow works hands-free and is safe to use in the car.
9. **Refine.** Adjust commands, accuracy, and export based on real use.
