"use strict"

document.addEventListener("DOMContentLoaded", function() {
    let start = 0
    let amount = 9
    getPosts(start, amount)

    window.addEventListener('scroll', function() {
        let windowRelativeBottom = document.documentElement.getBoundingClientRect().bottom
        if (windowRelativeBottom < document.documentElement.clientHeight + 50) {
            start += amount
            getPosts(start, amount)
        }
    })
})

function getPosts (start, amount) {
    fetch(`http://127.0.0.1:8000/app/posts?amount=${amount}&start=${start}`)
    .then (response => response.json())
    .then (json => showPosts(json))
}

function showPosts (posts) {
    const userPosts = document.querySelector('.user_posts')
    posts.forEach(post => {
        const img = document.createElement('img')
        img.src = post.image
        userPosts.append(img)
    })
}