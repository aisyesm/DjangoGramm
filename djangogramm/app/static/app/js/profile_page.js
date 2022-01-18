"use strict"

const curScriptElement = document.currentScript

document.addEventListener("DOMContentLoaded", function() {
    let start = 0
    let offset = 9
    let user_id = curScriptElement.getAttribute('user_id')
    let post_count = curScriptElement.getAttribute('post_count')
    const followData = JSON.parse(document.getElementById('follow-data').textContent)
    let canFollow = followData['can_follow']

    getPosts(start, offset, user_id)

    window.addEventListener('scroll', function() {
        let windowRelativeBottom = document.documentElement.getBoundingClientRect().bottom
        if (windowRelativeBottom < document.documentElement.clientHeight + 50) {
            start += offset
            if (start < post_count) {
                getPosts(start, offset, user_id)
            }
        }
    })

    if (canFollow) {
        const bio = document.getElementById('bio')
        const btnFollow = document.createElement('button')
        bio.after(btnFollow)
        let isFollowing = followData['is_following']
        setFollowOption(btnFollow, isFollowing)
        btnFollow.addEventListener('click', () => {
            isFollowing = !isFollowing
            setFollowOption(btnFollow, isFollowing)
        })
    }
})


function setFollowOption (btn, isFollowing) {
    if (!isFollowing) {
        btn.innerHTML = 'Follow'
        btn.className = 'action-btn btn btn-primary mb-4 mt-sm-2 mt-lg-3 px-4 px-md-5'
    }
    else {
        btn.innerHTML = 'Unfollow'
        btn.className = 'action-btn btn btn-danger mb-4 mt-sm-2 mt-lg-3 px-4 px-md-5'
    }
}


function getPosts (start, offset, user_id) {
    fetch(`${window.location.origin}/app/posts?user_id=${user_id}&offset=${offset}&start=${start}`)
    .then (response => response.json())
    .then (json => showPosts(json))
}


function showPosts (posts) {
    const userPosts = document.querySelector('.user_posts')
    posts.forEach(post => {
        const div = document.createElement('div')
        div.classList.add("post-area");
        const hyperlink = document.createElement('a')
        hyperlink.href = `${window.location.origin}/app/p/${post.id}`
        const img = document.createElement('img')
        img.src = post.image
        hyperlink.appendChild(img)
        div.appendChild(hyperlink)
        userPosts.append(div)
    })
}