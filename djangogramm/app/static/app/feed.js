"use strict"

const curScriptElement = document.currentScript

document.addEventListener("DOMContentLoaded", function() {
    let start = 0
    const offset = 7
    const total_num_posts = curScriptElement.getAttribute('total_num_posts')

    window.addEventListener('scroll', function() {
        let windowRelativeBottom = document.documentElement.getBoundingClientRect().bottom
        if (windowRelativeBottom < document.documentElement.clientHeight + 10) {
            start += offset
            if (start < total_num_posts) {
                getPosts(start, offset)
            }
        }
    })
})

function getPosts (start, offset) {
    console.log(`making fetch start = ${start} offset = ${offset}`)
    fetch(`http://127.0.0.1:8000/app/posts?offset=${offset}&start=${start}`)
    .then (response => response.json())
    .then (json => showPosts(json))
}

function showPosts (posts) {
    const userPosts = document.querySelector('.feed-container')
    posts.forEach(post => {
        const divPost = document.createElement('div')
        divPost.classList.add('post');

        const divUserPost = document.createElement('div')
        divUserPost.classList.add('post-user')

        const divAvatar = document.createElement('div')
        divAvatar.classList.add('avatar')
        const userAvatarLink = document.createElement('a')
        userAvatarLink.href = `http://127.0.0.1:8000/app/${post.user}/profile`
        const imgAvatar = document.createElement('img')
        imgAvatar.src = post.user_avatar
        userAvatarLink.append(imgAvatar)
        divAvatar.append(userAvatarLink)
        divUserPost.append(divAvatar)

        const divAuthor = document.createElement('div')
        divAuthor.classList.add('author')
        const userLink = document.createElement('a')
        userLink.href = `http://127.0.0.1:8000/app/${post.user}/profile`
        userLink.textContent = post.user_email
        divAuthor.append(userLink)
        divUserPost.append(divAuthor)

        const divPhoto = document.createElement('div')
        divPhoto.classList.add('photo')
        const imgPhoto = document.createElement('img')
        imgPhoto.src = post.image
        divPhoto.append(imgPhoto)

        const divCaption = document.createElement('div')
        divCaption.classList.add('caption')
        const pCaption = document.createElement('p')
        const spanCaption = document.createElement('span')
        spanCaption.classList.add('author')
        spanCaption.appendChild(userLink)
        pCaption.append(spanCaption, ` ${post.caption}`)
        divCaption.append(pCaption)

        const divDate = document.createElement('div')
        divDate.classList.add('date')
        const pDate = document.createElement('p')
        const months = {
                            1: "January",
                            2: "February",
                            3: "March",
                            4: "April",
                            5: "May",
                            6: "June",
                            7: "July",
                            8: "August",
                            9: "September",
                            10: "October",
                            11: "November",
                            12: "December"
                        }
        pDate.textContent = `${months[post.month]} ${post.day}, ${post.year}`
        divDate.append(pDate)

        divPost.append(divUserPost)
        divPost.append(divPhoto)
        divPost.append(divCaption)
        divPost.append(divDate)

        userPosts.append(divPost)
    })
}