const genreGrid = document.getElementById("genreselect");
const buttons = Array.from(genreGrid.children);

buttons.forEach(button => {
    button.addEventListener("click", (e) => {
        document.cookie = "genre=" + e.target.id; 
    })
});