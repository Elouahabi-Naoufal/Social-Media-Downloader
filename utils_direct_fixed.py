import re

def get_direct_download_url(url, platform, format_id, download_type):
    """Get direct download URL for client-side download"""
    try:
        import yt_dlp
        
        if download_type == 'video':
            ydl_opts = {
                'format': format_id,
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Get the direct URL
                direct_url = info.get('url')
                if not direct_url and info.get('formats'):
                    # Find matching format
                    for fmt in info['formats']:
                        if format_id == 'best' or fmt.get('format_id') == format_id:
                            direct_url = fmt.get('url')
                            break
                
                if direct_url:
                    # Clean filename
                    title = info.get('title', 'video')
                    clean_title = re.sub(r'[^\w\s-]', '', title)[:30]
                    clean_title = re.sub(r'[-\s]+', '_', clean_title)
                    
                    return {
                        'success': True,
                        'download_url': direct_url,
                        'filename': f"{platform}_{clean_title}.mp4"
                    }
                else:
                    return {'success': False, 'error': 'Could not get direct download URL'}
        else:
            # For audio, still need server processing
            from utils import download_media_with_format
            return download_media_with_format(url, platform, format_id, download_type)
            
    except Exception as e:
        return {'success': False, 'error': str(e)}