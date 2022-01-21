"use strict"

const curScriptElement = document.currentScript

document.addEventListener("DOMContentLoaded", function() {
    let start = 0
    const offset = 7
    getPosts(start, offset)
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
    fetch(`${window.location.origin}/app/posts?offset=${offset}&start=${start}`)
    .then (response => response.json())
    .then (json => showPosts(json))
}

function showPosts (posts) {
    const container = document.querySelector('.posts')
    posts.forEach(post => {
        const divPost = document.createElement('div')
        divPost.classList.add('card');
        divPost.style = 'border-radius: 10px; margin-bottom: 20px;'

        const divAuthorPost = document.createElement('div')
        divAuthorPost.classList.add('post-author')

        const divAvatar = document.createElement('div')
        divAvatar.classList.add('avatar')
        const userAvatarLink = document.createElement('a')
        userAvatarLink.href = `${window.location.origin}/app/${post.user}/profile`
        const imgAvatar = document.createElement('img')
        if (post.user_avatar) {
            imgAvatar.src = post.user_avatar
        }
        else {
            imgAvatar.src = "/static/app/img/empty_user.jpg"
        }
        userAvatarLink.append(imgAvatar)
        divAvatar.append(userAvatarLink)
        divAuthorPost.append(divAvatar)

        const divAuthor = document.createElement('div')
        divAuthor.classList.add('author')
        const userLink = document.createElement('a')
        userLink.href = `${window.location.origin}/app/${post.user}/profile`
        userLink.textContent = `${post.first_name} ${post.last_name}`
        divAuthor.append(userLink)
        divAuthorPost.append(divAuthor)

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
        const userLink1 = userLink.cloneNode(true)
        spanCaption.appendChild(userLink1)
        pCaption.append(spanCaption, ` ${post.caption}`)
        divCaption.append(pCaption)

        const divDate = document.createElement('div')
        divDate.classList.add('date')
        const pDate = document.createElement('p')
        pDate.textContent = `${post.pub_date}`
        divDate.append(pDate)

        divPost.append(divAuthorPost)
        divPost.append(divPhoto)
        divPost.append(divCaption)
        divPost.append(divDate)

        container.append(divPost)
    })
}