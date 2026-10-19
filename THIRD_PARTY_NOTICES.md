# Third-party notices

## FFmpeg

The Windows release bundles an FFmpeg executable from the BtbN FFmpeg Builds project, using its **win64 LGPL** build. FFmpeg is a separate third-party project and is not authored by 7TPCLAN.

- FFmpeg project: https://ffmpeg.org/
- FFmpeg source repository: https://github.com/FFmpeg/FFmpeg
- BtbN build project and release assets: https://github.com/BtbN/FFmpeg-Builds
- License: GNU Lesser General Public License (LGPL), version 2.1 or later. The license text is included beside the application as `COPYING.LGPLv2.1`.
- Build details are included beside the application in `FFMPEG-BUILD-NOTICE.txt`.

Nexus Capture uses FFmpeg's Windows desktop-capture input and the native MPEG-4 video encoder. The bundled build is intended to avoid requiring users to install FFmpeg or edit their PATH. The release workflow downloads the current BtbN LGPL build; users should consult the linked project for the build's exact source revision and license details.

FFmpeg is distributed without warranty, to the extent permitted by its license. All trademarks belong to their respective owners.
