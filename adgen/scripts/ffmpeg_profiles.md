\
# 9:16 vertical from 1024x1024 source (pad top/bottom)
ffmpeg -y -i hero1.png -vf "scale=1080:-2:flags=lanczos, pad=1080:1920:(ow-iw)/2:(oh-ih)/2" tt_9x16.mp4

# 1:1 square from 1920x1080 video (crop width)
ffmpeg -y -i ad_10s_16x9.mp4 -vf "crop=min(iw\,ih):min(iw\,ih):(iw-min(iw\,ih))/2:(ih-min(iw\,ih))/2, scale=1080:1080" ig_square.mp4

# 16:9 from image sequence
ffmpeg -y -r 24 -i kf_%04d.png -vf "scale=1920:-2:flags=lanczos" -c:v libx264 -pix_fmt yuv420p yt_16x9.mp4
