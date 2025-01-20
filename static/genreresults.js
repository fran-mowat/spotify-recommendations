const selectedGenre = document.cookie.split('=')[1];
let genreTitle = document.getElementById('genre'); 
genreTitle.innerHTML = 'Selected genre: ' + selectedGenre;