# Youtube-Soundbite-Extractor
A program that, given a Youtube channel ID or User ID, like *UCHugE6eRhqB9_AZQh4DDbIw* or *LinusTechTips*, grabs the all of the subtitles for a given channel (currently autosubs), and looks for a substring with which to extract an audio clip. Then it downloads the audio and uses an FFmpeg wrapper to clip the audio.

*Caveats:*
Unfortunately, the software is a bit naive at this point and will not clip out exactly the words you want, or may include other words around it, as I depend on Youtube's timecodes in order to split the audio. I may later add a capability to have finer control over the "phrase resolution" with TTS and some clever splitting.
###Prerequisites
```
 - Python 3
 - webvtt
 - youtube_dl
 - audioclipextractor
```
###Other Dependencies
```
 - FFmpeg
```
