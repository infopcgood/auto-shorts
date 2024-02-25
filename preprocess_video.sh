#!/bin/bash
ffmpeg -hwaccel cuda -i input.mp4 -vf fps=60,scale=2880:1920 -qp 0 -vcodec h264_nvenc out.mp4
ffmpeg -hwaccel cuda -i out.mp4 -vf "crop=1080:1920:900:0" -vcodec h264_nvenc -qp 0 out2.mp4
ffmpeg -i out.mp4 -c copy -map 0 -segment_time 00:01:00 -f segment -reset_timestamps 1 bgv/mp4/$1%03d.mp4
