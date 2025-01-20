async function sanitise_data() {
    let input_box = document.getElementById('playlist-input') 

    if (input_box.value.includes('/')) {
        playlist_id = input_box.value.split('/')[4].split('?')[0] 
        if (input_box.value.split('/')[2] == 'open.spotify.com' && input_box.value.split('/')[3] == 'playlist' && playlist_id.length == 22){
            input = 'valid'
        }

        else{
            input = 'invalid'
        }

    localStorage.setItem('playlist_id', playlist_id)
    localStorage.setItem('input', input)
    }
}

async function submit_playlist_id(playlist_id, input) { 
    playlist_id = localStorage.getItem('playlist_id')
    input = localStorage.getItem('input')

    if (input == 'valid'){ 
        const response = await fetch('/playlist', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'playlist_id': playlist_id})
        }).then((response) => {
            if (response.ok) { 
                window.location.href = '/playlistresults/' + playlist_id; 
            } else {
                alert('There was a problem with the playlist ID. Please check that the entered playlist is public to generate results.')
            }
        });
    }

    else if (input == 'invalid'){  
        alert('There was a problem with the playlist link entered. Please ensure that the link is given in the format: https://open.spotify.com/playlist/...')
    }   
}