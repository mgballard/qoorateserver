var qoorateConfig = {
    QOORATE_URI: 'http://qoorate.sethmurphy.com',
    QOORATE_API_URI: 'http://qoorate.sethmurphy.com/q',
    PROXY_URI: '/q_post.php',

    XHR_PROXY_URI: '/q/feed', // if client supports? not yet.
                              // would append QOORATE_URI
    XHR_UPLOAD_URI: '/q/uploader', // if client supports? not yet.
                                   // would append QOORATE_URI
    POST_MAX_LEN: 1000
}

var qoorateLang = {
    FLAG_SUCCESS: 'Thank you for your feedback.',
    SIGNIN: 'Sign in using',
    SIGNEDIN: 'Signed in via',    
    OK: 'OK',
    CANCEL: 'Cancel',
    LOGOUT: 'Log Out',
    CONTRIBUTION: 'Contribution',
    CONTRIBUTIONS: 'Contributions',
    SIGNIN_TO_CONTRIBUTE: 'Please sign in to make a contribution.',
    REMOVE: 'Remove',
    LINK: '1. Insert a link',
    TOPIC_COMMENT: 'Pose a Yes/No Question',
    COMMENT: 'Your Comment',
    IMAGE_COMMENT: 'Image Caption',
    POST_TO: 'Post to',
    REPLY_LINK_COMMENT: '2. Say something about your link',
    SHARE_COMMENT: 'comment about this share...',
    POST_BUTTON: 'Post',
    POST_TO_BUTTON: 'Post To',
    UPLOADER_NO_JAVASCRIPT: 'Please enable JavaScript to use file uploader.',
    SELECT_IMAGE: 'Select an Image',
    ATTACH_THUMBNAIL: 'Attach an Image Thumbnail',
    FLAG_ACTION_TYPES: [ [ '1', 'Spam' ], [ '2', 'Offensive' ], [ '3', 'Off Topic' ], [ '4', 'Disagree' ] ],
    SORT_ACTION_TYPES: [ [ '1', 'voting'], [ '2', 'recent'], [ '3', 'oldest'] ],
    LOGIN_TYPES: [ [ 'tw', 'Twitter', 'twitter' ], [ 'fb', 'Facebook', 'facebook' ], [ 'gp', 'Google+', 'googleplus' ] ]
} 
