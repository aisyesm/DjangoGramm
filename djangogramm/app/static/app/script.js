"use strict"

const curScriptElement = document.currentScript

document.addEventListener("DOMContentLoaded", function() {
    let start = 0
    let amount = 9
    let user_id = curScriptElement.getAttribute('user_id')
    let post_count = curScriptElement.getAttribute('post_count')
    getPosts(start, amount, user_id)

    window.addEventListener('scroll', function() {
        let windowRelativeBottom = document.documentElement.getBoundingClientRect().bottom
        if (windowRelativeBottom < document.documentElement.clientHeight + 50) {
            start += amount
            if (start < post_count) {
                getPosts(start, amount, user_id)
            }
        }
    })
})

function getPosts (start, amount, user_id) {
    fetch(`http://127.0.0.1:8000/app/posts?user_id=${user_id}&amount=${amount}&start=${start}`)
    .then (response => response.json())
    .then (json => showPosts(json))
}

function showPosts (posts) {
    const userPosts = document.querySelector('.user_posts')
    posts.forEach(post => {
        const div = document.createElement('div')
        div.classList.add("post-area");
        const hyperlink = document.createElement('a')
        hyperlink.href = `http://127.0.0.1:8000/app/p/${post.id}`
        const img = document.createElement('img')
        img.src = post.image
        hyperlink.appendChild(img)
        div.appendChild(hyperlink)
        userPosts.append(div)
    })
}