/*
**    @desc:        Qoorate Jquery
**    @author:    michael@mgbid.com
*/

function get_class_element(elem, pos) {
    //python style array operations (just getting end as of now)
    // SM: 20011219 - Was bombing out if no class attribute
    // Might be symptom of larger problem though, return null for now
    if(elem.attr('class') == null) {
        return null;
    }
    var class_arr = elem.attr('class').split(" ");
    var class_member = '';
    if (pos === -1) {
         class_member = class_arr[class_arr.length -1];
    }else{
        class_member = class_arr[pos];
    }
    return class_member;
}


// SM: 20111214 - to make sure broken images are not displayed
// for an img tag to use it you must add the attribute: onerror="ImgError(this, '/images/none.gif');"
// This must be done server side, by the time you set it i jquery, it is too late
function ImgError( source, url1, url2 ) {
    jQuery(source).load(function () {
        $this = jQuery(this);
        var $thisParent = $this.parents('.q_item .q_main_body .q_txt'),
            width = $thisParent.width();
        if($this.width() > width - 14) {
            $this.css('width', width - 14);
        }
    });

    source.src = url1;
    if(url2) {
        source.onerror = "ImgError(this, '" + url2 + "')";
    } else {
        source.onerror = "";
    }
    return true;
}


jQuery(document).ready(function($) {

    /* Our "global" vars */
    // GD moved for availability in sort
    var location_md5 = jQuery('#q_').attr('class');
    
    //close the sort drop down if its open
    jQuery('body').click(function(){
        jQuery('#q_sort_list').css('visibility', 'hidden');
    });


    // SM: Assign function to variable in function scope to keep out of global namespace
    // SM: 20120106 - This get called on load
    var init = function() {
        addLastItemClassToChildren( jQuery('#q_cmnt_contents') ); // add a class to style our last children
        // resize our width for narrow screens
        call_theme_function('dynamicResize_pre')
        if (call_theme_function('dynamicResize') == false){
            dynamicResize();
        }
        call_theme_function('dynamicResize_post')
        
        // Setup our overlay divs for popups
        call_theme_function('createOverlay_pre')
        if (call_theme_function('createOverlay') == false){
            createOverlay();
        }
        call_theme_function('createOverlay_post')


        // Setup all our events
        call_theme_function('wireEvents_pre')
        if (call_theme_function('wireEvents') == false){
            wireEvents();
        }
        call_theme_function('wireEvents_post')
        // SM: 20120114 - we need unicode support
        // $.ajaxSetup({ contentType: "charset=utf-8" });

        // Attach error to anything, we will just display a message
        // this is needed when using $.post
        jQuery( "#q_" ).ajaxError(function(e, jqxhr, settings, exception) {
          if(jqxhr.responseText.length > 0) {
            errorMsg(jqxhr.status, jqxhr.responseText);
          }
        });
        call_theme_function('ready')        
    }


    var call_theme_function = function (func_name, args) {
        try{
            var theme_func = eval(qoorateConfig.THEME + "_" + func_name);
            if (theme_func != 'undefined'){
                if(args){
                    theme_func.apply(this, args);
                }   else {
                    theme_func.apply(this);
                }
                return true;
            }
        }catch(err){
            // do nothing
            return false;
        }
        return false;
    }
    
    // resizes our width if we are on a narrow screen
    var dynamicResize = function() {
        // Dynamically set our width for smaller screens if needed.
        var s_width = window.innerWidth;
        if( s_width < 675 ) {
            styleMobile(true);
            rescaleImages();
        }else{
            styleMobile(false);
            rescaleImages();        
        }
 
    }

    // style for mobile stylesheet 
    // really just add a class and let css do it's magic
    var styleMobile = function(enabled) {
      var $q = jQuery('#q_');
      if ( enabled ) {
        $q.addClass('mobile');
      } else {
        $q.removeClass('mobile');
      }
    }

    // MB: 20110103 - adds the l class to last children for rounded bottom corners
    // SM: 20110112 - moved from init to function for use when getting more items dynamically  too
    // SM: 20110123 - also responsible for displaying/hiding the toggle button now too
    var addLastItemClassToChildren = function($block) {
           var $children = $block.find('.q_item.c');
           $children.removeClass('l');
           $children.removeClass('lm');

           $children.each(function() { 
                var $this = jQuery(this);
                var $nextitem = $this.next();
                if( $nextitem != null && $nextitem.length > 0 ) {
                    if( !$nextitem.hasClass('c') ) {
                        if($nextitem.hasClass('more_link_child') ) {
                            $this.addClass('lm');
                        }
                        $this.addClass('l');

                        var $previtem = $this.prev();
                        // see if we should hide our toggle button
                        if ( $previtem.hasClass('lv-1') ) {
                            // we are an only child
                            $this.find('.q_toggle').css('display','none');
                        }else{
                            $this.find('.q_toggle').css('display','block');
                        }
                    }
                } else {
                     // we have no next item, so we are last
                        if ( $previtem == null || $previtem.hasClass('lv-1') ) {
                            // we are an only child
                            $this.find('.q_toggle').css('display','none');
                        }else{
                            $this.find('.q_toggle').css('display','block');
                        }
                     jQuery(this).addClass('l');
                }
    
         });
    }


    var images_to_rescale = 0;
    var images_rescaled = 0;
    var resize_job;
    // reset the width of our images if they are too big
    var rescaleImages = function() {
        var $images = jQuery('#q_ .q_main_body .q_img img, #q_ .q_main_body .q_img a img');
        var $image = null;
        images_to_rescale = $images.length
        images_rescaled = 0;
        for( var i = 0; i < $images.length; i++ ) {     
            $image = jQuery($images[i]);
    
            $image.load(function () {
                images_rescaled++;
                $this = jQuery(this);
                var $thisParent = $this.parents('.q_item .q_main_body'),
                    width = $thisParent.width();
                
                if(qoorateConfig.GRID_COLUMNS) {
                    var cols = qoorateConfig.GRID_COLUMNS,
                    col_trim = qoorateConfig.GRID_COLUMN_TRIM,
                    col_width = width / cols - col_trim;
                }


                if($this.width() > width - 14) {
                    $this.css('width', width - 14);
                }
                if(resize_job){
                    clearTimeout(resize_job);
                }
                if(images_to_rescale == images_rescaled){
                    position();
                }else{
                    resize_job = setTimeout( position, 100);
                }
            });
        }
    }


    // refresh our page - used for after login
    var reload = function () {

        var uri = window.location.href;

        // remove trailing '#' if needed
        var indexAt = uri.indexOf("#") 
        if ( indexAt > -1 ) { uri = uri.substring( 0, indexAt ); }
         
        uri += "#q_";

        // reload the page
        window.location.href = uri;
        window.location.reload();
    }

    // A wrapper for scrollToObject
    var scrollToItem = function(q_short_name, item) {
        if(item) {
            var $item = jQuery( "#" + q_short_name + "-" + item.id );        
            if ( $item.length > 0 )
                scrollToObject($item);
        }
    }


    var scrollToObject = function ( $item ) {
        try {
            var item_top = $item.offset().top,
                item_height = $item.height(),
                item_bottom = item_top + item_height,
                scrollY = Math.max( (window.scrollY?window.scrollY:0), 
                                    (document.body.scrollTop?document.body.scrollTop:0), 
                                    (document.body.parentNode.scrollTop?document.body.parentNode.scrollTop:0) ),
                w_height = window.innerHeight;

            var scrollTo = -1;

            if( item_top < scrollY || item_bottom > ( scrollY + w_height ) ) {
                if ( item_height > w_height ) {
                    scrollTo = item_top;
                } else {
                    scrollTo = item_bottom - w_height;
                }
            }

            if( $item.length > 0 && scrollTo > -1 ) {
                jQuery( 'html, body' ).animate( {
                    scrollTop: scrollTo
                }, 200 );
            }
        } catch (e) {
            ; // do nothing
        }

    }


    // SM: 20111219 - needed now that content is being passed in JSON field
    var urldecode = function( str ) {
        // was messed up by comic book swear #$%@!!
        // so now we escape, then unescape content too
        //return decodeURIComponent( ( str + '' ).replace( /\+/g, '%20' ) );
        return unescape(decodeURIComponent( escape(( str + '' ).replace( /\+/g, '%20' )) ));
    }

    // SM: 20111223 - Check the length of an input and display status
    var displayInputLength = function ( $inputElement, maxLength) {
        if( maxLength ) {
            var $inputLengthDisplay = $inputElement.parent().find( ".inputLength" );
            // using jquery resizable adds extra parent, compensate
            if ($inputLengthDisplay.length == 0)
                $inputLengthDisplay = $inputElement.parent().parent().find( ".inputLength" );
            if( $inputLengthDisplay.length > 0 ) {
                var preVal = $this.data( "preVal" );
                var remainingCharacters = '';
                if( preVal != $inputElement.val() ) {
                    remainingCharacters = maxLength - $inputElement.val().length;
                }
                if ( remainingCharacters < 0 ) {
                    if ( ! $inputLengthDisplay.hasClass( "over" ) ) {
                        $inputLengthDisplay.addClass( "over" );
                    }
                } else {
                    $inputLengthDisplay.removeClass( "over" );
                }
                $inputLengthDisplay.html( remainingCharacters );
            }
        }
        return;
    }


    // SM: 20111223 - Replace the content, while preserving the old
    // Use restoreContent to restore the $content
    // relies on content having same unique ids to match equality
    var replaceContent = function( $content, $newContent, animationDuration) {
        // detach our content
        var $parent = $content.parent();
        var childIndex = 0;
        var $siblings = $parent.children();
        var $child = null;

        // get the child index of our content
        for ( var i = 0; i < $siblings.length; i++ ) {
            $child = jQuery( $siblings[i] );
            if( $child.attr("id") == $content.attr("id") ) {
                childIndex = i;
                break;
            }
        }

        // we may want a callback, we may not
        var doReplace = function(){
             // detach our original content and save it in the new content along with the child index
            var $originalContent = null;
            if($content.data("originalContent") == null ) {
                $content.detach();
                $originalContent = $content;
            } else {
                $originalContent = $content.data("originalContent");
                $content.remove();  
            }
            // SM: 20120105 - Original content is always the first replaced
            $newContent.data("originalContent", $originalContent);
            $newContent.hide();
            // place the new content in the same position as the old content
            if( childIndex == 0 ) {
                $parent.prepend($newContent);
            } else {
                var $siblingBefore = jQuery( $parent.children()[ childIndex - 1 ] );
                $siblingBefore.after( $newContent );
            }
            $newContent.show(animationDuration);
        };

        // see if we want animation with a a callback
        if ( animationDuration > 0 ) {
            $content.fadeOut(animationDuration, doReplace);
        }else {
            doReplace();
        }
    }


    // SM: 20111223 - Content must have been replaced with replaceContent()
    var restoreContent = function( $content, animationDuration) {
        var $originalContent = $content.data( "originalContent" );
        if ( $originalContent == null ) 
            return false;

        var $parent = $content.parent();
        var childIndex = 0;
        var $siblings = $parent.children();
        var $child = null;

        // get the child index of our content
        for ( var i = 0; i < $siblings.length; i++ ) {
            $child = jQuery( $siblings[i] );
            if( $child.attr("id") == $content.attr("id") ) {
                childIndex = i;
                break;
            }
        }

        var doRestore = function() {
            $content.remove();
            $originalContent.show();
            // place the new content in the same position as the removed content
            if( childIndex == 0 ) {
                $parent.prepend( $originalContent );
            } else {
                var $siblingBefore = jQuery( $parent.children()[ childIndex - 1 ] );
                $siblingBefore.after( $originalContent );
            }
        };

        // remove our content, for good!
        if ( animationDuration > 0 ) {
            $content.fadeOut(animationDuration, doRestore);
        } else {
            doRestore();
        }
    }


    // SM: 20111227 - Update the cn-xx class
    var updateChildCNOrderClass = function($data) {
        var sequence = 1;
        var $item = null;
        var cn = null;
        var item_class = null;
        for ( var i = 0; i < $data.length; i++ ) {
            $item = jQuery($data[i]);
            if ( $item.hasClass('c') ) {
                cn = 'cn-' + sequence ++;
                item_class = $item.attr( 'class' ).replace( /cn-[0-9]*/, cn );
                $item.attr( 'class', item_class );
                $data[ i ] = $item[ 0 ];
            }
        }
        return $data; 
    }


    //SM: 20111227 - Restore our preVal values in inputs
    var restorePrevals = function( $block ) {
        var $inputs = $.merge( $block.find( "textarea" ), $block.find( "input" ) );
        var preVal = null;
        var $input = null;
        for ( var i = 0 ; i < $inputs.length ; i++ ) {
            $input = jQuery($inputs[i]);
            preVal = $input.data("preVal");
            if( preVal != null ) {
                $input.val(preVal);
            }

        }
    }

    var getSortActions = function( _id ) {
      var sort_actions_html='';
      var sort_actions = qoorateLang.SORT_ACTION_TYPES;
      var action_type;
      var sort_action;
      for (var i=0; i < sort_actions.length; i++) {
            sort_action = sort_actions[i];
            action_value = sort_action[0];
            action_type = sort_action[1];
            sort_actions_html += '<li class="q_sort_list"><a href="#" class="do action sort ' + _id + ' order-' + action_value + '">' + action_type + '</a></li>';
      }
      return sort_actions_html;
    }



    // SM: 20111228 - Get our flag actions as links
    var getFlagActions = function( _id ) {
        var flag_actions_html = '';
        var flag_action_types = qoorateLang.FLAG_ACTION_TYPES;
        var machine_type;
        var display_type;
        for ( var i = 0; i < flag_action_types.length ; i++ ) {
            value_type = flag_action_types[ i ][ 0 ];
            display_type = flag_action_types[ i ][ 1 ];
            role_type = flag_action_types[ i ][ 2 ];
            machine_type = display_type.toLowerCase().replace( ' ', '_' );
            flag_actions_html += '<a href="#" id="' + machine_type + '-' + _id + '" ' +
                                     'class="do action flag ' + _id + ' ' + machine_type + ' value-' + value_type + ' role-' + role_type + '">' +
                                display_type +
                            '</a>';
        }
        return flag_actions_html;
    };

    // SM: 20111228 - Get our flag actions as links
    var getLoginActions = function( _id ) {
        var html = '';
        var login_types = qoorateLang.LOGIN_TYPES;
        var login_type;
        var value_type;
        var display_type;
        html += '<div class="loginOptions">' + 
                '<div class="q_inr">' +
                '<span class="ttl">' + qoorateLang.SIGNIN + '</span>';
        for ( var i = 0; i < login_types.length ; i++ ) {
            login_type = login_types[ i ];
            value_type = login_type[ 0 ];
            display_type = login_type[ 0 ];
            html += '<div class="loginButtonWrapper">' +
                    '<a class="login ' + value_type + '"><span>' + display_type + '</span></a>' +
                    '</div>';
        }
        html += '<div class="q_clear"></div>' + 
                '</div>' + 
                '</div>';

        return html;
    };



    /* Stare overlay methods */

    // SM: 20110106 - Add a div for our overlays
    // The transparent overlay itself is seperate than the overlay popup
    var createOverlay = function() {
        jQuery('body').prepend('<div id="q_overlay" style="display: none;"></div>' + 
                          '<div id="q_overlay_content" style="display: none;"></div>');
    };


    // SM: 20110106 - Show an overlay
    var showOverlay = function($html) {
        var $overlay = jQuery('#q_overlay');
        var $overlayContent = jQuery('#q_overlay_content');
        if( $html.hasClass('error') ) {
            $overlayContent.addClass('error');
        } else {
            $overlayContent.removeClass('error');
        }
        var body = document.body,
            html = document.documentElement;
        var full_height = Math.max( body.scrollHeight, body.offsetHeight, 
                               html.clientHeight, html.scrollHeight, html.offsetHeight );
                               
        // set our height to be the whole screen
        $overlay.height(full_height);

        if ( $overlay != null && $overlayContent != null && $html != null ) {
            $overlayContent.html($html);
            // fade us out so we can display and position properly
            $overlayContent.fadeTo(0,0);

            // closure for our fadeIn call back
            var getAdjustPosition = function($overlay, $overlayContent){
                return function() {
                    // position us verticaly in the center
                    // css will take care of our horizontal posion
                    var c_height = $overlayContent.height(),
                        w_height = window.innerHeight,
                        scroll_y = Math.max( (window.scrollY?window.scrollY:0), 
                                              (document.body.scrollTop?document.body.scrollTop:0), 
                                              (document.body.parentNode.scrollTop?document.body.parentNode.scrollTop:0) ),
                        o_top = ( (w_height - c_height) / 2 ) + scroll_y;

                    $overlayContent.css('top', o_top);

                    var c_width = $overlayContent.width();
                    var o_width = $overlay.width();
                    var o_left = (o_width - c_width) / 2;
                    $overlayContent.css('left', o_left);
                    // now that we are positioned, fade us in
                    $overlayContent.fadeTo(250, 1);
                };
            }; 

            // fade in, opacity only will show
            // callback will set vertical position properly
            $overlay.fadeIn(250, getAdjustPosition( $overlay, $overlayContent ) );
            //$overlayContent.fadeIn(250, getAdjustPosition( $overlayContent, $html ) );

            if ( window.innerHeight > $overlay.height() ) {
                $overlay.height(window.innerHeight);
            }
         }
    };


    // SM: 20110106 - Hide our overlayContent, then our overlay
    var closeOverlay = function(callback, source) {
        var $overlay = jQuery('#q_overlay');
        var $overlayContent = jQuery('#q_overlay_content');

        var getFadeOutOverlay = function( $overlay, callback, source ) {

            var getFadeOutOverlayContent = function( callback, source ) {
                if ( callback != null ) {
                    callback.call( source );
                }
            };

            return function() { 
                                $overlay.fadeOut(250, getFadeOutOverlayContent( callback, source ) ); 
                              };
        }

        $overlayContent.fadeOut( 250, getFadeOutOverlay( $overlay, callback, source ) );

   };
    

    // SM: 20110106 - Our error message overlay
    var showErrorOverlay = function(error, message, onCloseCallback) {
        var $html = jQuery('<div class="overlayContent error">' + 
                        '<div class="contentMessage"><span class="error" style="display: none;">[ ' + error + ']</span> ' + message + '</div>' +
                        '<div class="contentButtons">' + 
                            '<a class="dialog ok"><span>' + qoorateLang.OK + '</span></a>' + 
                        '</div>' +
                    '</div>');
        $html.find('.dialog.ok').click( function() { 
                                                        closeOverlay(onCloseCallback); 
                                                   } 
                                      );
        
        showOverlay($html);
    };


    // SM: 20110106 - Our error message overlay
    var showMessageOverlay = function(message, onCloseCallback) {
        var $html = jQuery('<div class="overlayContent message">' + 
                        '<div class="contentMessage">' + message + '</div>' +
                        '<div class="contentButtons">' + 
                            '<a class="dialog ok"><span>' + qoorateLang.OK + '</span></a>' + 
                        '</div>' +
                    '</div>');
        $html.find('.dialog.ok').click( function() { 
                                                        closeOverlay(onCloseCallback); 
                                                   } 
                                      );
        
        showOverlay($html);
    };


    // SM: 20110106 - Our unauthorized message overlay
    // Includes login buttons
    var showLoginOverlay = function(error, message, onLoggedInCallback) {
        var $html = jQuery('<div class="overlayContent error">' + 
                        '<div class="contentMessage">' + message + '</div>' +
                        getLoginActions() + 
                        '<div class="contentButtons">' + 
                            '<a class="dialog cancel"><span>' + qoorateLang.CANCEL + '</span></a>' + 
                        '</div>' +
                    '</div>');

        var getLoginCallback = function( provider, onLoggedInCallback ){
            return function() {
               oAuthLogin(provider, onLoggedInCallback);
               closeOverlay(); 
            };
        };
     
        $html.find('a.dialog.cancel').click( function() { closeOverlay(); } );

        var login_types = qoorateLang.LOGIN_TYPES;
        var value_type;
        for ( var i = 0; i < login_types.length ; i++ ) {
            value_type = login_types[ i ][ 0 ];
            $html.find('a.login.' + value_type).click( getLoginCallback( value_type, onLoggedInCallback ) );
        }

        showOverlay($html);
    };


    /* end overlay methods */


    // SM: 20111228 - Given a tag and a string of classes the value is returned
    // class is assumed to be in the format [tag]-[value]
    // [tag] = the tag passed to the function
    // [value] = the value returned by the function
    var getValueFromClasses = function (tag, klasses) {
        // our flagTypeId is stored as a  class prepended with 'value_' in the anchor that caused this doPost()
        klasses = klasses.split(' ');
        var klass = null;
        var value = null;
        var key_value = null;
        for ( var i = 0; i < klasses.length; i ++) {
            klass = klasses[ i ];
            key_value = klass.split('-');
            if( key_value[0] == tag ) {
                value = key_value[1];
                break;
            }
        }
        return value;
    };


    // Validate our replyLink input and change form appropriately
    var validateReplyLink = function($replyLink){
           var rVal = false;
           var $thisParent = $replyLink.parents('.dyn');
           var $attachLink = $thisParent.find( 'a.attachLink' );
           if ( event.which == 13 ) {
               $attachLink.click();
           } else {
               if( isURL( $replyLink.val() ) ) {
                   $attachLink.removeClass("disabled");
               }else if ( $attachLink.length > 0 ) {
                   $attachLink.addClass("disabled");
               }
           }

           // MB: 20110103 - allow post w/out link thumbnail BEGIN
           var charCount = $thisParent.find('.inputLength').text();
           var maxLength = $thisParent.find('input.replyLink').data("maxLength");
           if( (charCount >= 0) && (!$attachLink.hasClass('disabled')) ) {
               $thisParent.find('a.addItem').removeClass('disabled');
           } else if ( $attachLink.length > 0 ) {
               $thisParent.find('a.addItem').addClass('disabled');
           }
           // MB: 20110103 - allow post w/out link thumbnail END
    };


    // Validate the form after a text area action
    var textareaValidateAction = function($textarea) {
        var $textareaParent = $textarea.parents('.dyn');
        if ( $textarea.hasClass( 'action' ) ) {
            if ( $textarea.hasClass( 'replyComment' ) || $textarea.hasClass('replyTopic') ||
                 $textarea.hasClass('replyLink') || $textarea.hasClass('replyPhoto') || $textarea.hasClass('share') ) {
                var $addItem = $textareaParent.find( 'a.addItem' ),
                    preVal = $this.data("preVal"),
                    maxLength = $textarea.data("maxLength");
                
                if ( $addItem.length == 0) {
                    $addItem = jQuery( 'a.shareItem' );
                }
                // SM: 20111214 - Would we want enter key behavior in a textarea?
                // For now, no.
                if ( false && event.which == 13 ) {
                    $addItem.click();
                } else {
                    //console.log($this.val());
                    if( ($textarea.val() != '' && $textarea.val() != preVal || $addItem.hasClass('shareItem') ) &&
                        // SM: 20120104 - We don't care about having a thumbnail anymore
                        (
                            (!$textarea.hasClass('replyLink') || jQuery(".contribUI_Wrap").length > 0 ) ||
                            // But we do need a somewhat valid link
                            (!$textarea.hasClass('replyLink') || isURL( $textareaParent.find('input.replyLink').val() ) )
                        ) &&
                        (!$textarea.hasClass('replyPhoto') || jQuery(".q_qq-uploader ul li.q_qq-upload-success").length > 0 ) &&
                        ( !maxLength || $textarea.val().length <= maxLength)
                      ) {
                        $addItem.removeClass("disabled");
                    }else{
                        if ( ! $addItem.hasClass( "disabled" ) ) {
                            $addItem.addClass("disabled");
                        }
                    }
                    if( maxLength ) {
                        displayInputLength($textarea, maxLength);
                    }
                }
            }
        }
    };

    // used for callbacks
    var getHideDynamicForm = function( _block, interval ) {
        return function(){
            if( ! _block.hasClass( 'dyn' ) ) {
                _block = _block.find( '.dyn' );
                _block.slideUp( interval, getPositionCallback() );
            }
        };
    };

    var getRemoveBlock = function( _target, interval ) {
        return function(){
            _target.slideUp( interval, getRemoveCallback(_target) );
        };
    };

    var getRemoveCallback = function( _remove_target ) {
        return function(){
            _remove_target.remove();
            position();
        };
    };

    var getPositionCallback = function( ) {
        return function(){
            position();
        };
    };
 
    // SM: 20111228 - Moved from doPost
    // GD: 20110102 - Moved from a click function for availability in sort onchange
    var handleResponse = function( $source_object, _q_short_name,_item,_id,_action,_block,_location ) {
        return function(data) {
            if(data) {
                // SM: 20120107 - Moved parsing message to new function
                var parsed_data = parseJSONresponse(data);
                var data_object = parsed_data[0];
                data = parsed_data[1];
                // SM:" 20120122 - make sure we have a data object
                if ( data_object == null) {
                     // we should probable figure out why we ...
                     console.log("null data_object: " + _action);
                } else {
                    if ( data_object.error > 0 ) {
                        errorMsg(data_object.error, data_object.message);
                    } else {
                        updateContributions( data_object.contributions );
                    }

                    /*mgb nov23 */
                    // SM: 20111219 - upVote and downVote handled with same code now
                    if(_action == 'upVote' || _action == 'downVote') { // SM: 20111219 - removed && _block.hasClass('c') to handle topic votes
                        if( data_object.error == 0 ) {

                            changeVote(data_object, _block); // SM: 20111219 - added JSON result to call to get vote numbers from
                            var parent_votes = data_object.parent_votes;

                            if(parent_votes) { // SM: 20111220 - Update our parent vote count too
                                changeVote( parent_votes, jQuery( "#" + parent_votes.q_short_name + "-" + parent_votes.id ) );
                            }
                        }
                        $source_object.removeClass('disabled');
                    } else if ( _action == 'flag' ) {
                        // just restore our flag options back to the icon
                        // restoreContent( jQuery( $source_object.parent(), 495 ) );
                        // we are in dynForm now
                        if( ! _block.hasClass('dyn') )
                            _block = _block.find('.dyn:first');

                        restorePrevals(_block);

                        
                        var $message =jQuery('<div class="footerMessage">' + qoorateLang.FLAG_SUCCESS + '</div>');

                        if( data_object.error == 0 ) {
                            _block.before( $message );
                            setTimeout( getRemoveBlock($message, 250 ), 2000 );
                        }
                        _block.hide();
                        position();
                        return;

                    } else if ( _action == 'deleteItem' ) {
                        if( data_object.error == 0 ) {
                            _block.after( $message );
                            setTimeout( getRemoveBlock($message, 250 ), 2000 );
                            
                            // put a message in the header, and give us a message
                            _block = jQuery('#' + data_object.q_short_name + '-' + data_object.item.id);
                            var $message =jQuery('<div class="q_item lv-1 footerMessage">' + qoorateLang.DELETE_SUCCESS + '</div>');
    
                            _block.remove();
                            var deleted_related_item_ids = eval(data_object.deleted_related_item_ids);
                            for (var i=0; i < deleted_related_item_ids.length; i++){
                                related_item_id = deleted_related_item_ids[i];
                                jQuery('#' + data_object.q_short_name + '-' + related_item_id).remove();
                            }
                            // now remove all our children
                            position();
                        }
                        return;
                    } else if ( _action == 'shareItem' ) {

                        $reply_button = jQuery('.' + data_object.q_short_name + '-' + data_object.item.id + '.do.makeForm.reply span:first');
                        $reply_button.html(qoorateLang.REPLY_BUTTON)
                        childToggleControls($reply_button);


                        if( ! _block.hasClass('dyn') )
                            _block = _block.find('.dyn:first');

                        restorePrevals(_block);

                        
                        var $message =jQuery('<div class="footerMessage">' + qoorateLang.SHARE_SUCCESS + '</div>');

                        if( data_object.error == 0 ) {
                            _block.before( $message );
                            setTimeout( getRemoveBlock($message, 250 ), 2000 );
                        }
                        _block.hide();
                        position();
                        return;
                    } else {
                        if( data != null && data != '' ) {
                            var $data = jQuery(data),
                                close_dyn_form = true;
                            if(_action == 'sort') {
                                jQuery('#q_cmnt').css('visibility', 'hidden');
                                jQuery('#q_cmnt_contents').children().remove();
                                jQuery('#q_cmnt_contents').append($data);
                                jQuery('#q_cmnt').css('visibility', 'visible');
                                position();
                                addLastItemClassToChildren( jQuery('#q_cmnt_contents') );
                                return false;
                            }

                            restorePrevals(_block);

                            if (_block.hasClass('dyn')) {
                                // SM: 20111217 - Prepend new comment to top of list for immediate gratification
                                jQuery('#q_cmnt_contents').prepend($data);
                                // SM: added callback to scroll to item
                                var item = data_object.item;
                                var q_short_name = data_object.q_short_name;
                                _block.slideUp('250',function() { 
                                        position();
                                        scrollToItem(q_short_name, item); 
                                    } );
                                // See if we are an img and need to be resized
                                var item = data_object.item;
                                if(item.type==1){
                                    jQuery('#' + data_object.q_short_name + '-' + item.id + ' .q_img' + ' img').load(function () {
                                        $this = jQuery(this);
                                        var $thisParent = $this.parents('.q_item .q_main_body .q_txt'),
                                            width = $thisParent.width();
                                        if($this.width() > width - 14) {
                                            $this.css('width', width - 14);
                                        }
                                    });
                                }

                                return false;
                            }

                            if(_action == 'getMore') {
                                jQuery('.getMore').remove();
                                var $comments = jQuery('#q_cmnt_contents');
                                childToggleControls($data);
                                $comments.append($data);
                                addLastItemClassToChildren( $comments );
                                position();
                                return false;
                            }
    
                            if (_action == 'logoffUser') {
                                // re-enable our logoff buttons
                                jQuery('.q_inr.logged-in').attr('class', 'q_inr');
                                jQuery('#q_cmnt').attr('class', 'anon');
                                jQuery('#q_ .q_head_wrap').attr('class', 'q_head_wrap');
                             //   jQuery('#q_fllw').html('<div class="q_inr"><span class="ttl">+ Follow</span></div>'); 
                                jQuery('#q_socl .ttl.signin').html(qoorateLang.SIGNIN);
                                jQuery('#q_socl .ttl.logoff').html('');
    
                                // SM: 20120112 - destroy any dynamic forms we may have had from another login
                                jQuery('#q_ .dyn').fadeOut(250, function(){
                                                jQuery('#q_ .dyn').html('');
                                                });
    
                               return false;
                            }

                            var q_short_name = data_object.q_short_name, p_id = 0;

                            if ( !jQuery('#'+_id).hasClass('lv-1') ) {
                                $parent = jQuery('#'+_id).parent('.lv-1');
                                p_id = getValueFromClasses('co', _block.attr('class'));
                                if($parent.length==0) {
                                    $parent = jQuery('#' + q_short_name + '-' + p_id);
                                } else {
                                    close_dyn_form = false;
                                }
                                jQuery('.co-' + p_id).remove();

                                if($parent.find('.q_item.c').length > 0 || $data.find('.q_item.c').length > 0){
                                    $data = $data.find('.q_item.c');
                                    child_embedded = 1;
                                }else{
                                    $data = $data.slice(1);
                                }

                                if(child_embedded>0) {
                                    $parent.append($data);
                                } else {
                                    $parent.after($data);
                                }
                            } else if ( jQuery('#'+_id).hasClass('lv-1') ) {
                                var child_class = 'p_' + _id,
                                    child_embedded = 0;
                                $parent = jQuery('#'+_id);
                                if($parent.find('.q_item.c').length > 0 || $data.find('.q_item.c').length > 0){
                                    $data = $data.find('.q_item.c');
                                    child_embedded = 1;
                                }else{
                                    $data = $data.slice(1);
                                }
                                $children = jQuery('.' + child_class);
                                if ( $children.length > 0 ) {
                                    $children.remove();
                                    if(child_embedded>0) {
                                        $parent.append($data);
                                        // close_dyn_form = false;
                                    } else {
                                        $parent.after($data);
                                    }
                                } else {
                                    if(child_embedded > 0) {
                                        $parent.append($data);
                                    } else {
                                        $parent.after($data);
                                    }
                                }
                            }
                            // update our parents reply count if we have it
                            $replycount = jQuery('#' + q_short_name + '-' + p_id + ' .replycount');
                            $replycount.html(data_object.replycount);
                            $toggle = $parent.find('.replyWrapper:first');
                            childToggleControls($toggle, data_object.replycount);
                            if(_action == "addItem" && data_object.replycount > 0){
                                //show our replies
                                $toggleButton = jQuery('#toggle_' + $parent.attr('id'));
                                if($toggleButton.hasClass('expand')) {
                                    $toggleButton.click()
                                }
                            }
                            // SM: 20111220 - We now have information on the new item
                            // This greatly simplifies our scrolling behavior
                            // SM: 20111214 - We need the slideUp now that we removed the "hover" slideup
                            addLastItemClassToChildren( jQuery('#q_cmnt_contents') );
                            var $slide_up_block = _block.find( ".dyn"),
                                item = data_object.item,
                                q_short_name = data_object.q_short_name;

                            if(close_dyn_form) {
                                if ( item ) {
                                    if (child_embedded) {
                                        // we need to un-pretty up our reply button
                                        var $replyWrapper =$parent.find('.replyWrapper');
                                        $replyWrapper.find('.inner.active').removeClass('active')
                                        $replyWrapper.find('.reply.active').removeClass('active')
                                    }
                                    $slide_up_block.slideUp('250', function() {
                                        position();
                                        scrollToItem( q_short_name, item ); 
                                        } );
                                }
                            } else {
                                position();
                                scrollToItem( q_short_name, item ); 
                            }
                        }
                    }

                    /*
                    else {
                          jQuery('.dyn.'+_id).slideUp(250, function() { 
                          jQuery('#q_cmnt_contents').fadeOut(250, function() {
                                jQuery(this).remove();
                                jQuery('#q_cmnt').hide();
                                         //slideUp(2000);
                          $.get(qoorateConfig.PROXY_URI, function(data) {
                            if (jQuery('#q_cmnt_contents')) jQuery('#q_cmnt_contents').remove();
                            $q_all = jQuery(data).find('#q_cmnt');
                            jQuery('#q_cmnt').append($q_all.html());
                            jQuery('#q_cmnt').fadeIn(250);
                            });
                          });
                        });
    
                    }*/

                }
            }
        }
    };


    var doMakeForm = function(_q_short_name,_item,_id,_form) {
        console.log("doMakeForm");
        // we need this function to exist to build our form itself
        call_theme_function('doMakeForm', [_q_short_name,_item,_id,_form])

        // SM: 20111214 - Attach our preVals to our inputs
        var $allInputs = jQuery('.dyn.' + _id + ' :input');
        for ( var i = 0; i < $allInputs.length; i++ ) {
            var $input = jQuery($allInputs[i]);
            var type = $input.attr('type');
            if(type != "checkbox" && type != "submit") {
                preVal = $input.data("preVal");
                if( ! preVal )
                    $input.data("preVal", $input.val());
            }
        }

        // SM: 20111223 - Attach our max length to all our inputs
        for ( var i = 0; i < $allInputs.length; i++ ) {
            var $input = jQuery($allInputs[i]);
            var type = $input.attr('type');
            if(type != "checkbox" && type != "submit") {
                $input.data("maxLength", qoorateConfig.POST_MAX_LEN);
            }
        }



        // SM: 20111214 - Now use preVal attached to input element
        jQuery("textarea")
            .focus(function() {
                var $this = jQuery(this);
                var preVal = $this.data('preVal');

                if( preVal == $this.val() )
                    jQuery(this).val('');
            })
            .blur(function() {
                 var $this = jQuery(this);
                 var preVal = $this.data('preVal');
                 if( $this.val() == '' ) {
                     $this.val(preVal);
                 } 
        });

        // SM: 20111214 - Now use preVal attached to input element
        jQuery("input")
            .focus(function() {
                var $this = jQuery(this);
                var preVal = $this.data('preVal');

                if( preVal == $this.val() )
                    jQuery(this).val('');
            })
            .blur(function() {
                 var $this = jQuery(this);
                var preVal = $this.data('preVal');
                 if( $this.val() == '' ) {
                     $this.val(preVal);
                 } 
        });

    };


    var skyscraper_doMakeForm = function(_q_short_name,_item,_id,_form) {
        console.log("skyscraper_doMakeForm");
        var form_html = '';

        var topicText = qoorateLang.TOPIC_COMMENT;
        var commText = qoorateLang.COMMENT;
        var imgText = qoorateLang.IMAGE_COMMENT;

        if(_form == 'replyLink')
            commText = qoorateLang.REPLY_LINK_COMMENT;
        else if( _form == 'share' )
            commText = qoorateLang.SHARE_COMMENT;
 
        // SM: 20111223 - Added display for remaining characters left before max reached
        var inputLength = '<span class="inputLength">' + qoorateConfig.POST_MAX_LEN + '</span>';
        var commentTextarea = '<div class="textAreaWrap-outer ' + _form + '">' + 
                                '<div class="textAreaWrap-inner">' +
                                    '<textarea name="replyComment" class="do action ' + _form+' '+_id+'">' + commText + '</textarea>' +
                                    inputLength + 
                                '</div>' +
                              '</div>';
        var topicTextarea = '<div class="textAreaWrap-outer ' + _form + '">' +
                                '<div class="textAreaWrap-inner">' +
                                    '<textarea name="replyTopic" class="do action ' + _form + ' ' + _id + '">' + topicText + '</textarea>' +
                                    inputLength +
                                '</div>' +
                            '</div>';
        //var commentTextarea2 = '<div class="textAreaWrap-outer ' + _form + '"><div class="textAreaWrap-inner"><textarea name="replyComment" class="do action ' + _form + ' ' + _id + '">' + topicText + '</textarea>' + inputLength + '</div></div>';
        var imageTextarea = '<div class="textAreaWrap-outer ' + _form + '">' +
                                '<div class="textAreaWrap-inner">' +
                                    '<textarea name="replyComment" class="do action ' + _form+' '+_id+'">' + imgText + '</textarea>' +
                                    inputLength +
                                '</div>' +
                            '</div>';

        var social = get_class_element(jQuery('#q_socl .logged-in'),2);
        var login_types = qoorateLang.LOGIN_TYPES;
        var login_type;

        for (var i=0; i < login_types.length; i++) {
          login_type = login_types[i];
          if(social == login_type[0]) { 
            social = login_type[1];
            break;
          }
        }

        var postTo = '<span class="postTo">' +
                        '<input class="post_to" type="checkbox" checked="checked" name="post_to" value="post_to" />' +
                        '<label for="post_to">' + qoorateLang.POST_TO + ' ' + social + '</label>' +
                     '</span>';

        var postAnonymous = '';
        if (qoorateConfig.ANONYMOUS_CAPABLE === true) {
            var postAnonymous = '<span class="isAnonymous">' +
                            '<input class="is_anonymous" type="checkbox" name="is_anonymous" value="1" />' +
                            '<label for="is_anonymous">' + qoorateLang.POST_ANONYMOUS +'</label>' +
                            '<label for="nickname" style="display: none">' + qoorateLang.NICKNAME +'</label>' +
                            '<input type="textbox" class="nickname" name="nickname" style="display: none;" value="' + qoorateLang.DEFAULT_NICKNAME + '">' +
                         '</span>';
        }
        
        // our default action, submit button label and state
        var actionType = 'addItem';
        var actionLabel = qoorateLang.POST_BUTTON;
        if($this.parents().is('.q_head_wrap')) {
            actionLabel = qoorateLang.PUBLISH_BUTTON;
        }
        var disabled = ' disabled';
        if ( _form == 'replyLink' ) {
            form_html = formHtml(_form, _id, qoorateLang.LINK, commentTextarea);
        } if ( _form == 'replyTopic' ) {
            form_html = topicTextarea;
        } else if ( _form == 'replyComment' ) {
            form_html = commentTextarea;
        } else if ( _form == 'share' ) {
            // Don't display our social post_to checkbox and change the action and label for the submit button
            postTo = '<input class="post_to" type="hidden" name="post_to" value="post_to" />';
            postAnonymous = '';
            actionType = 'shareItem';
            actionLabel = qoorateLang.POST_TO_BUTTON + ' ' + social;
            disabled = '';
            form_html = commentTextarea;
        } else if ( _form == 'replyPhoto' ) {
            var photoId = _id + '-q_qq';
            form_html = imageTextarea + '<div id="' + photoId  + '">' +
                                            '<noscript>' +
                                                '<p>' + qoorateLang.UPLOADER_NO_JAVASCRIPT + '</p>' +
                                                '<!-- uploader goes here -->' +
                                            '</noscript>' +
                                        '</div>';
        }
        
        var form_action = '<a class="do action ' + actionType + ' '+ _id + ' submit' + disabled + '" href="#">' +
                          '<span>' + actionLabel + '</span>' +
                          '</a>';

        if ( _form == 'flag' ) {
            form_action = '<div id="flag_' + _id + '" class="flagAreaWrapper-outer ' + _id + '">' +
                        getFlagActions( _id ) +
                        '</div>';
            form_html = '';
            postTo = '';
            postAnonymous = '';
        }

        var $dynForm = jQuery('.dyn.'+_id);
        if ( $dynForm.html() == '' ||
             $dynForm.parents().is('.q_head_wrap') ||
             $dynForm.find("." + actionType).length ==0 
           ) {

            // SM: 20111214 - Create link now defaults to disabled, and now has a var that can be changed
            // SM: 20120104 - Cancel button now lives outside the div so it can be positioned with float only
            var form = form_html + 
                        '<div class="dynFormFooter">' + postTo + postAnonymous + 
                        form_action + 
                        '<br class="q_clear" />' + 
                        '</div>' +
                        '<a class="do x" href="#">x</a><div class="q_clear"></div>';
            $dynForm.html(form).fadeIn('250',function() { 
                if(_form == 'replyPhoto') {
                    //console.log(photoId);
                    createUploader(photoId);
                    jQuery('#'+photoId).append('<input id="photoHash" name="thumbnailLarge" type="hidden" />' +
                                          '<input id="replyPhoto" name="replyPhoto" type="hidden" value="" />');
                }
                scrollToObject($dynForm);
            });

        } else {
            $dynForm.fadeIn('250', function() {
                scrollToObject($dynForm);
            });
        }

    };



    var grid_doMakeForm = function(_q_short_name,_item,_id,_form) {
        console.log("grid_doMakeForm");
        var form_html = '';

        var topicText = qoorateLang.TOPIC_COMMENT;
        var commText = qoorateLang.COMMENT;
        var imgText = qoorateLang.IMAGE_COMMENT;

        $reply_button = jQuery('.' + _q_short_name + '-' + _item + '.do.makeForm.reply span:first');
        if(_form == 'replyLink') {
            commText = qoorateLang.REPLY_LINK_COMMENT;
            $reply_button.html(qoorateLang.REPLY_BUTTON)
            childToggleControls($reply_button);
        } else if( _form == 'share' ) {
            commText = qoorateLang.SHARE_COMMENT;
            qoorateLang.REPLY_BUTTON = $reply_button.html();
            $reply_button.html(qoorateLang.SHARE_BUTTON);
        }
 
        // SM: 20111223 - Added display for remaining characters left before max reached
        var inputLength = '<span class="inputLength">' + qoorateConfig.POST_MAX_LEN + '</span>';
        var commentTextarea = '<div class="textAreaWrap-outer ' + _form + '">' + 
                                '<div class="textAreaWrap-inner">' +
                                    '<textarea name="replyComment" class="do action ' + _form+' '+_id+'">' + commText + '</textarea>' +
                                    inputLength + 
                                '</div>' +
                              '</div>';
        var topicTextarea = '<div class="textAreaWrap-outer ' + _form + '">' +
                                '<div class="textAreaWrap-inner">' +
                                    '<textarea name="replyTopic" class="do action ' + _form + ' ' + _id + '">' + topicText + '</textarea>' +
                                    inputLength +
                                '</div>' +
                            '</div>';
        //var commentTextarea2 = '<div class="textAreaWrap-outer ' + _form + '"><div class="textAreaWrap-inner"><textarea name="replyComment" class="do action ' + _form + ' ' + _id + '">' + topicText + '</textarea>' + inputLength + '</div></div>';
        var imageTextarea = '<div class="textAreaWrap-outer ' + _form + '">' +
                                '<div class="textAreaWrap-inner">' +
                                    '<textarea name="replyComment" class="do action ' + _form+' '+_id+'">' + imgText + '</textarea>' +
                                    inputLength +
                                '</div>' +
                            '</div>';

        var social = get_class_element(jQuery('#q_socl .logged-in'),2);
        var login_types = qoorateLang.LOGIN_TYPES;
        var login_type;

        for (var i=0; i < login_types.length; i++) {
          login_type = login_types[i];
          if(social == login_type[0]) { 
            social = login_type[1];
            break;
          }
        }

        var postTo = '<span class="postTo">' +
                        '<input class="post_to" type="checkbox" checked="checked" name="post_to" value="post_to" />' +
                        '<label for="post_to">' + qoorateLang.POST_TO + ' ' + social + '</label>' +
                     '</span>';

        var postAnonymous = '';
        if (qoorateConfig.ANONYMOUS_CAPABLE === true) {
            var postAnonymous = '<span class="isAnonymous">' +
                            '<input class="is_anonymous" type="checkbox" name="is_anonymous" value="1" />' +
                            '<label for="is_anonymous">' + qoorateLang.POST_ANONYMOUS +'</label>' +
                            '<label for="nickname">' + qoorateLang.NICKNAME +'</label>' +
                            '<input type="textbox" class="nickname" name="nickname" style="display: none;" value="' + qoorateLang.DEFAULT_NICKNAME + '">' +
                         '</span>';
        }

        // our default action, submit button label and state
        var actionType = 'addItem';
        var actionLabel = qoorateLang.POST_BUTTON;
        if($this.parents().is('.q_head_wrap')) {
            actionLabel = qoorateLang.PUBLISH_BUTTON;
        }
        var disabled = ' disabled';
        if ( _form == 'replyLink' ) {
            form_html = formHtml(_form, _id, qoorateLang.LINK, commentTextarea);
        } if ( _form == 'replyTopic' ) {
            form_html = topicTextarea;
        } else if ( _form == 'replyComment' ) {
            form_html = commentTextarea;
        } else if ( _form == 'share' ) {
            // Don't display our social post_to checkbox and change the action and label for the submit button
            postTo = '<input class="post_to" type="hidden" name="post_to" value="post_to" />';
            postAnonymous = '';
            actionType = 'shareItem';
            actionLabel = qoorateLang.POST_TO_BUTTON + ' ' + social;
            disabled = '';
            form_html = commentTextarea;
        } else if ( _form == 'replyPhoto' ) {
            var photoId = _id + '-q_qq';
            form_html = imageTextarea + '<div id="' + photoId  + '">' +
                                            '<noscript>' +
                                                '<p>' + qoorateLang.UPLOADER_NO_JAVASCRIPT + '</p>' +
                                                '<!-- uploader goes here -->' +
                                            '</noscript>' +
                                        '</div>';
        }

        var form_action = '<a class="do action ' + actionType + ' '+ _id + ' submit' + disabled + '" href="#">' +
                          '<span>' + actionLabel + '</span>' +
                          '</a>';

        if ( _form == 'flag' ) {
            form_action = '<div id="flag_' + _id + '" class="flagAreaWrapper-outer ' + _id + '">' +
                        getFlagActions( _id ) +
                        '</div>';
            form_html = '';
            postTo = '';
            postAnonymous = '';
        }

        var $dynForm = jQuery('.dyn.'+_id);
        $dynForm.html("");
        if ( $dynForm.html() == '' ||
             $dynForm.parents().is('.q_head_wrap') ||
             $dynForm.find("." + actionType).length ==0 
           ) {

            // SM: 20111214 - Create link now defaults to disabled, and now has a var that can be changed
            // SM: 20120104 - Cancel button now lives outside the div so it can be positioned with float only
            var form = '<a class="do x" href="#">x</a>' + form_html + 
                        '<div class="dynFormFooter ' + _form + '">' + postTo + postAnonymous + 
                        form_action + 
                        '<br class="q_clear" />' + 
                        '</div>' +
                        '<div class="q_clear"></div>';
            $dynForm.html(form).fadeIn('250',function() { 
                if(_form == 'replyPhoto') {
                    //console.log(photoId);
                    createUploader(photoId);
                    jQuery('#'+photoId).append('<input id="photoHash" name="thumbnailLarge" type="hidden" />' +
                                          '<input id="replyPhoto" name="replyPhoto" type="hidden" value="" />');
                }
                scrollToObject($dynForm);
                $dynForm.find('textarea').focus();
                $dynForm.find('#q_replyLink').focus(); 
            });

        } else {
            $dynForm.fadeIn('250', function() {
                scrollToObject($dynForm);
            });
        }
        $dynForm.show();

        jQuery(".q_item textarea").resizable({
            resize: function(event, ui) {
                    position(); 
                },
            handles: "s"
        });        
        var $pi = $dynForm.closest('.q_item.lv-1'),
            $rb = $pi.find('#reply_' + _id),
            is_active = $rb.hasClass('active'),
            $p = $rb.parent(),
            $toggleReply = $p.find('.toggleReply');
        // No longer show children with reply
        //$pi.addClass('active');
        $rb.addClass('active');
        $p.addClass('active');

        // No longer show children with reply
        //if($toggleReply.hasClass('expand')){
        //    is_active = false;
        //}
        //$toggleReply.removeClass('expand');
        //$toggleReply.addClass('contract');
        //$toggleReply.find('span').html(qoorateLang.TOGGLE_OFF);

        //if(!is_active){
        position();
        //}        

    };

    var formHtml = function(formType, id, value, textAreaType) {

        var $fhtml = '';

        if( formType == 'replyLink' ) {
            $fhtml = jQuery('<div><div class="dynReplyWrap">' +
                        '<div class="inputAreaWrap-outer ' + formType + '">' +
                            '<div class="inputAreaWrap-inner">' +
                                '<input id="q_'+formType+'" name="' + formType + '" class="do action ' + formType+' ' + id + '" value="' + value + '" />' +
                            '</div>' +
                        '</div>' + 
                        textAreaType + 
                    '</div></div>');
             // moved attach button after url input
             $fhtml.find('#q_' + formType).after('<a href="#" class="do action attachLink ' + id + ' disabled" >Add Thumbnail</a>' +
                                                 '<div class="q_clear"></div>');
        } else {
            $fhtml = jQuery('<div class="dynReplyWrap">' +
                        '<div class="inputAreaWrap-outer ' + formType + '">' +
                            '<div class="inputAreaWrap-inner">' +
                                '<input id="q_'+formType+'" name="' + formType + '" class="do action ' + formType+' ' + id + '" value="' + value + '" />' +
                            '</div>' +
                        '</div>' + 
                        textAreaType + 
                    '</div>');
        }

        return $fhtml.html();

    };


    var attachContent =  function (id, $loading, $replyLink) {

        // place here for closure in callback
        // SM: 20110105 - We now replace with loading instead of disable
        // var $replyLink = jQuery('input.replyLink');
        // var $replyLinkWrapper =  $replyLink.parent();
        // var $attachLink = jQuery('a.attachLink');
        var $elem = jQuery( '.dyn.' + id).find(".dynReplyWrap");

        return function(data) {
            if (data instanceof Object) {
                
            } else { 
                if ( data[0] != '{' ) {
                   var datas = data.split('\r\n\r\n');
                   if( datas.length > 1) {
                       data = datas[1];
                   } else {
                      data = datas[0];
                   }
                }
                data = $.parseJSON(data);
            }

            if ( data.error > 0) {
                // SM: 20111219 - Display an error now
                errorMsg(data.error, data.message);
                // SM: 20110105 - We now replace with loading instead of disable
                //$replyLinkWrapper.removeClass('disabled'); 
                //$replyLink.removeClass('disabled');
                //$attachLink.removeClass('disabled');

                 //$elem.append('<div class="contribUI_Wrap"><div class="contribUI_Content"><div class="contribUI_Title"><h2>'+jQuery('input.replyLink').val()+'</h2></div></div></div>');
                // jQuery('.contribUI_Content').css('position','');
                // SM: 20120122 - we now use restoreContent instead
                //hideLoader();
                restoreContent($loading);
                return;
            }

           var $contribHTML = jQuery('<div class="contribUI_Wrap">' + 
                                    '<div class="contribUI_Image"><ul></ul></div>' + 
                                    '<div class="contribUI_Content">' + 
                                        '<div class="contribUI_Title"> <h2></h2> </div>' + 
                                        '<div class="contribUI_Summary"> <p></p> </div>' + 
                                        '<div class="contribUI_Cntrls">' + 
                                            '<div class="contribUI_Checkbox">' + 
                                                '<input id="attach_image_thumbnail" type="checkbox" ' +
                                                        'name="attach_image_thumbnail" value="true" style="display: none;" /> ' + 
                                                'No image to attach.' +                                                
                                                '<a href="#" class="remove_link">' + qoorateLang.REMOVE + '</a>' +
                                            '</div>' +
                                        '</div>' + 
                                        '<input type="hidden" name="replyLink" class="replyLink" value="' + validateURL($replyLink.val()) + '"/>' +
                                    '</div>' +
                                '</div>' );

            // SM: 20111223 - Move to same area link was entered
            // Used new replaceContent() function
            //$elem.append( $contribHTML );
            replaceContent($loading, $contribHTML, 0)

            if( data.description == '' && data.images.length == 0 ) $contribHTML.find('.contribUI_Wrap').remove();

            if ( data.title == '' ) {
                $contribHTML.find('.contribUI_Title').append($replyLink.val());
                if( data.images.length == 0) hideLoader();
            } else {
                $contribHTML.find('.contribUI_Title h2').append(data.title);
            }

            var summary = data.description;

            if( summary ) {
                if ( summary.length > 150 ) {
                    var summary = summary.trim().substring(0,150).split(" ").slice(0,-1).join(" ") + "...";
                }
            }

            $contribHTML.find('.contribUI_Summary p').append(summary);
            if(data.images) {
                if( data.images.length > 0 ) {
                    $contribHTML.find('.contribUI_Image').attr('id','slider');
                    $contribHTML.data('current', -1);
                    $contribHTML.data('count', 0);
                    imgsLoad(data.images, id, $contribHTML,$elem);
                }
                // SM: 20121114 replace our text for the link input
                // Then disable the attach button
                var preVal = $replyLink.data("preVal");
                $replyLink.val(preVal);
                // SM: 20110105 - We now replace with loading instead of disable
                // $replyLinkWrapper.removeClass('disabled');
                // $replyLink.removeClass('disabled');
                // $attachLink.addClass('disabled');
            } else {
                errorMsg(0, "Invalid URL!");
            }
        }
    };


    // called on our first acceptable image, setups slide control
    var createSliderControls = function( $contribHTML, $elem ) {
        var contribControlsInnerHtml =  '<div class="contribUI_Buttons">' + 
                                            '<a href="javascript:void(0)" id="prevBtn" class="contribUI_Left"></a>' + 
                                            '<a href="javascript:void(0)" id="nextBtn" class="contribUI_Right"></a>' + 
                                        '</div>' + 
                                        '<div class="contribUI_Text">' +
                                            '<div class="contribUI_PageNumber">' + 
                                                '<span class="contribUI_PageNumber_Current"></span>' + 
                                                '  of ' +
                                                '<span class="contribUI_PageNumber_Total"></span>' + 
                                            '</div>' +
                                            '<div class="contribUI_SelectImage">' + qoorateLang.SELECT_IMAGE + '</div>' +
                                        '</div>' + 
                                        '<div class="q_clear"></div>' +
                                       '<div class="contribUI_Checkbox">' + 
                                            '<input id="attach_image_thumbnail" type="checkbox" ' +
                                                    'name="attach_image_thumbnail" value="true" checked="checked" /> ' + 
                                            '<label for="attach_image_thumbnail" id="label_attach_image_thumbnail">' +
                                                qoorateLang.ATTACH_THUMBNAIL +
                                            '</label>' +
                                            '<div class="q_clear_left"></div>' +
                                        '</div>' +
                                        '<div class="contribUI_Remove">' + 
                                            '<a href="#" class="remove_link">' + qoorateLang.REMOVE+ '</a>' +
                                             '<div class="q_clear_right"></div>' +
                                        '</div>' +
                                        '<div class="q_clear"></div>';
 

        $contribHTML.find(".contribUI_Cntrls").html( contribControlsInnerHtml );
        // SM: 20121215 - this is now in imgLoad on image success
        // $coontribHTML.find('.contribUI_PageNumber_Total').append(ln);
        // $contribHTML.find('.contribUI_PageNumber_Current').append(count);

        // SM: 20121215 - we now use data values attached to contrib div
        $contribHTML.find('#nextBtn').bind('click', function() {
            var $slider = $contribHTML.find(".contribUI_Wrap").find('#slider');
            var current = $contribHTML.data('current');
            var count = $contribHTML.data("count");
            if( current + 1 >= count ) {
                return false;
            } else {
                current += 1;
                $contribHTML.data("current", current);
                $contribHTML.find('.contribUI_PageNumber_Current').text(current + 1);
                $contribHTML.find('#slider ul').animate({marginLeft : current * 100 * -1});
            }
        });

        $contribHTML.find('#prevBtn').click(function() {
            var $slider = $contribHTML.find(".contribUI_Wrap").find('#slider');
            var current = $contribHTML.data('current');
            var count = $contribHTML.data('count');
            if( current == 0) {
                return false;
            } else {
                current -= 1;
                $contribHTML.data("current", current);
                $contribHTML.find('#slider ul').animate({marginLeft : current * 100 * -1});
                $contribHTML.find('.contribUI_PageNumber_Current').text(current + 1);
            }
        });

        function getChange(id) {
            return function() {

                if($contribHTML.find('#attach_image_thumbnail').is(':checked')) {
                    $contribHTML.find('.contribUI_Image img').eq(count-1).css('visibility', 'visible');
                } else {
                    $contribHTML.find('.contribUI_Image img').eq(count-1).css('visibility', 'hidden');
                }

                textareaValidateAction( jQuery('textarea.replyLink.' + id) );
            };
        };

        $contribHTML.find('#attach_image_thumbnail').change(getChange());

        // SM: 20121119 - enable create if we already have a comment
        var $replyComment = $elem.find( "textarea.replyLink" );
        var preVal = $replyComment.data( "preVal" );
        var $addItem = $elem.find( "a.addItem" );
        //console.log($replyComment.val());

        if( $replyComment.val() != '' && $replyComment.val() != preVal ) {
            $addItem.removeClass( "disabled" );
        } else {
            $addItem.addClass("disabled");
        }
    };

    // the gatekeeper for images to include for attached links
    var imgsLoad = function(imgArray, id, $contribHTML, $elem) {
        function getForEach(id, $contribHTML, $elem) {
            return function(intIndex, objVal) {
               // create and load img in memory first
               var $img =  jQuery('<img />');
               function getImgLoad(id, $contribHTML, $elem) {
                    return function() {
                        var img_width = this.width;
                        var img_height = this.height;
                        // SM: 20120114 - added ratio back into the mix
                        ratio = img_width / img_height;
                        if ( !( (img_height < 40 && img_width < 40) || ratio > 4 || ratio < .25 ) ) {
                            var $this = jQuery(this);
                            // SM: 20120114 - we need to set current/count here now that it is based on success
                            if($contribHTML.data('current') == -1){
                                // we are our first succesful image
                                createSliderControls( $contribHTML, $elem );
                                $contribHTML.data('current', 0);
                                $contribHTML.find('.contribUI_PageNumber_Current').text(1);
                                textareaValidateAction( jQuery('textarea.replyLink.' + id) );
                            }
                            var count = $contribHTML.data("count") + 1;
                            $contribHTML.data('count', count);
                            $contribHTML.find('.contribUI_PageNumber_Total').text(count);
                       
                            if ( img_width > 100 || img_width <= 50 ) {
                                $this.attr('width', 100);
                            }else{
                                pad = Math.floor((100 - img_width)/2);
                                $this.css({paddingLeft : pad});
                            }

                            var $slider_ul = $contribHTML.find('ul'); 
                            var $image_li = jQuery('<li id="shareImg-'+intIndex+'"></li>');
                            $image_li.html($this);
                            $contribHTML.find('ul').css("width", (count * 100) + "pc");
                            $slider_ul.append($image_li);
 
                       }
                       hideLoader();
                    }
                };
                $img.load(getImgLoad(id, $contribHTML, $elem));
                $img.attr('src', objVal);
            };
        };
        $.each(imgArray, getForEach(id, $contribHTML, $elem) );
        //console.log();
    };


    var hideLoader = function() {
       //jQuery('.imgLoad').slideUp('slow');//fadeOut('slow');
       jQuery('.imgLoad').remove();
    };

    var filterImage = function(img) {
        if (img.height() && img.height() < 40) {
            img.remove();
        }
    };


    var addImages = function(index, val) {
        jQuery('.contribUI_Image').append('<img class="contibUI_Single_Image" src='+val+' id="'+index+'" />');
    };


    // SM: 20111229 - added source object as first parameter
    var doPost = function($source_object, _q_short_name, _item, _id, _action, _block, _location) {
        //    console.log("q_short_name:"+_q_short_name);
        //    console.log("item:"+_item);
        //    console.log("id:"+_id);
        //    console.log("action:"+_action);
        //    console.log("class:"+_class);
        //console.log("action:" + _action);
        // SM: 20111230 - Eveything we look for should be within our form
        var $dynForm = jQuery('.dyn.' + _id);
        var $allInputs = $dynForm.find(':input');

        if( _action != 'attachLink') {
            // SM: 20111214 - Remove any preVal text from "blank" fields
            for (var i = 0 ; i < $allInputs.length; i++ ) {
                var $input = jQuery($allInputs[i]);
                var preVal = $input.data('preVal');
                if( preVal != null && $input.val() == preVal ) {
                    $input.val('');
                }
            }
        }
        //console.log("action:" + _action);

        var _query = $allInputs.serializeArray();
        _query.push({ "name":"action",    "value":_action});
        _query.push({ "name":"location",    "value":_location});
        _query.push({ "name":"referer", "value":window.location.href}); // SM: we need this to ('replyTopic')post a link on social shares
        _query.push({ "name":"q_short_name",    "value":_q_short_name});
        _query.push({ "name":"QOOID",    "value":$.cookie('QOOID')});
        _query.push({ "name":"QOOTID",    "value":$.cookie('QOOTID')});


        if ( _action=='flag' ) {
            var flagTypeId = getValueFromClasses( 'value', $source_object.attr( 'class' ) );
            _query.push({"name":"flagTypeId","value":flagTypeId });
            _query.push({"name":"itemId", "value":_item });
        }

        if ( _action=='deleteItem' ) {
            _query.push({"name":"itemId", "value":_item });
        }

        if ( _action=='shareItem' ) {
            _query.push({"name":"itemId", "value":_item });
        }


        if(_item) {
            _query.push({ "name":"relatedId",    "value":_item});
        }

        if ( _action == 'addItem' && $dynForm.find('.contribUI_Cntrls').length > 0 ) {
            var $contribHTML = $dynForm.find('.contribUI_Wrap');
            var $slider = $contribHTML.find('#slider ul');
            // SM: 20120115 - get our position from the data
            //
            //var imgPos = -1*(($slider.css('marginLeft').replace("px","")/10)/($slider.width()/100));
            var imgPos = $contribHTML.data('current');
            
            if($dynForm.find('#attach_image_thumbnail').is(':checked')) {
                _query.push( {"name":"thumbnailLarge", "value": $slider.find('img').eq(imgPos).attr('src')} );
            }
            if($dynForm.find('input.is_anonymous').is(':checked')) {
                _query.push({ "name":"nickname",    "value":$dynForm.find('input.is_anonymous').parent().find('input.nickname')});
            }
        }

        if (_action == 'getMoreChildren') {
            _query.push({"name":"parentId", "value":_item});
        }

        if (_action == 'getMore') {
            _id = parseInt(_id) + qoorateConfig.PARENT_PAGE_SIZE;
            _query.push({"name":"moreIndex", "value":_id});
            var sort = jQuery('#q_sort_by').val();
            _query.push({"name":"sort", "value":sort});
        }
        if (_action == 'sort' ) {
           var sort = jQuery('#q_sort_by').val();
           _query.push({"name":"sort", "value":sort});
        }
        if(_action == 'attachLink') {
           _query[0]["value"] = validateURL(_query[0]["value"]);
            var $replyLink = $dynForm.find('input.replyLink');
            var $replyLinkParent = jQuery($replyLink.parent());
            if ($dynForm.find('.contribUI_Wrap')) {
                $dynForm.find('.contribUI_Wrap').remove();

                // SM: 20121114 Now just disable until success
                //jQuery('input.replyLink').val('');
                // SM: 20110105 - We now replace with loading instead of disable
                // $replyLinkParent.addClass('disabled');
                // $replyLink.addClass('disabled');
                // $dynForm.find('a.attachLink').addClass('disabled');
            }
            var $loading = jQuery('<div class="contribUI_Wrap"><div class="imgLoad"><div align="center"><img src="' + qoorateConfig.QOORATE_API_URI + '/img/load.gif" /></div></div></div>');

            // SM: 20120104 - Moved loading image
            //jQuery('div.' + _id).prepend(loading_html);
            replaceContent($replyLinkParent, $loading);
            // SM: 20121114 Added complete and error handlers
            // Needed to change from post to ajax
            // SM: 20120114 - changed back to post, need unicode suppost
            /*
            $.ajax( {
                type: 'POST',
                url: qoorateConfig.PROXY_URI,
                data: _query,
                success: attachContent(_id, $loading, $replyLink),
                contentType: "charset=utf-8",
                error: function (xhr, error) { 
                    errorMsg(0, error);
                    $replyLink.removeClass('disabled');
                },
                complete: function() {
                    $replyLink.removeClass('disabled');
                } 
            });
            */
            $.post( qoorateConfig.PROXY_URI, _query, attachContent( _id, $loading, $replyLink) );
            //.complete( function() {
            //    $replyLink.removeClass('disabled');
            //}); 

            //removeImages();
        } else {
            //console.log(_block);
            //console.log("action:" + _action);
            $.post(qoorateConfig.PROXY_URI, _query, handleResponse( $source_object, _q_short_name,_item, _id, _action, _block, _location ));
            //.complete( function() {
            //    $replyLink.removeClass('disabled');
            //}); 

       }
        return false;
    };


    // SM: 20111219 - removed _action from method signature and replaced with data
    // Now uses counts returned from server to update all votes as necessary
    var changeVote = function(data, _block) {
        //console.log("votesUp" + data.votesUp);
        //console.log("votesDown" + data.votesDown);
        var tally = _block.find('.upVote span'); 
        //console.log(_block);
        //console.log(tally);
        // SM: 20111219 - Now uses split and join, assuming first item is the vote count for votes with suffix labels
        var tally_val = tally.text().split(" ");
        //console.log(tally_val);
        if(tally_val[0] != data.votesUp) {
            tally_val[0] = data.votesUp;
            //console.log(tally_val[0]);
            //console.log(tally_val.join(" "));
            var upTally = tally_val.join(" ");
            tally.fadeOut(250,function() {jQuery(this).text(upTally).fadeIn(); } )
        }

        tally = _block.find('.downVote span');
        tally_val = tally.text().split(" ");
        if(tally_val[0] != data.votesDown) {
            tally_val[0] = data.votesDown;
            var downTally = tally_val.join(" ");
            tally.fadeOut(250,function() {jQuery(this).text(downTally).fadeIn(); } )
        }

    };


    var authenticate = function() {
        var allInputs = jQuery('#logsign').find(':input');
        console.log(allInputs);
        var _query = allInputs.serializeArray();
            _query.push({ "name":"action",    "value":"authentication"});
            _query.push({ "name":"QOOID",    "value":$.cookie('QOOID')});
            _query.push({ "name":"QOOTID",    "value":$.cookie('QOOTID')});

        $.post(qoorateConfig.PROXY_URI, _query, function(data) {
                    console.log(data);
                },'json');
    };


    var isURL = function(textval) {
        if ( ! textval )
            return false;

        var expression = /[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#&//=]*)?/gi;
        var regex = new RegExp(expression);
        return regex.test(textval);
    };


    var validateURL = function(textval) {
        var urlregex1 = new RegExp("^(http:\/\/|https:\/\/){1}([0-9A-Za-z]+\.)"),
            urlregex2 = new RegExp("^(http:\/\/www.|https:\/\/www.|ftp:\/\/www.|www.){1}([0-9A-Za-z]+\.)");
        if (!urlregex2.test(textval)) {
            if (!urlregex1.test(textval)) {
                textval = "http://"+textval;
                // SM: 20121214 - now return false if not valid
                if (!urlregex2.test(textval) && !urlregex1.test(textval)) { return false; }
            }
        }
        return textval;
    };


    var errorMsg = function(error, message) {
        // no callback, this slipped through and came from the server
        if(error == '401') {
            showLoginOverlay(error, message);
        }else {
            showErrorOverlay(error, message) ;
        }
    };

    // SM: 20120109 - performs a callback to do the action that was prohibited upon succesfull login
    var authError = function(error, message, callback) {
        showLoginOverlay(error, message, callback);
    };


    var updateContributions = function(contrib_count) {
         if (typeof(contrib_count)=='number'&&parseInt(contrib_count)==contrib_count &&contrib_count > 0) {
             $elem = jQuery("#q_cntr .ttl");
             $lbl = contrib_count;
             if(contrib_count == 1) {
                 $lbl += " " + qoorateLang.CONTRIBUTION;
             }else{
                 $lbl += " " + qoorateLang.CONTRIBUTIONS;
             }
             $elem.text($lbl);
         }else{
            // do nothing
         }
    };


    var createUploader = function(id) {
        var uploader = new qq.FileUploader({
            element: document.getElementById(id),
            action: qoorateConfig.PROXY_URI + '?action=uploader',
            debug: true,
            onComplete: function(id, fileName, responseJSON) { 
                                                                if( jQuery('.q_qq-upload-success').length > 0 ) { 
                                                                    var preImg = '<img src="' + qoorateConfig.QOORATE_API_URI + '/uploader/images/' + responseJSON.hash + '">'
                                                                    jQuery('.q_qq-upload-success').prepend('<span class="q_qq-upload-file-preview">' + preImg + '</span>');
                                                                    var $replyPhoto = jQuery('.do.action.replyPhoto');
                                                                    var preVal = $replyPhoto.data("preVal");
                                                                    if ( preVal && $replyPhoto.val() != preVal ) {
                                                                        jQuery(".do.action.addItem").removeClass("disabled");
                                                                    } else {
                                                                        jQuery(".do.action.addItem").addClass("disabled");
                                                                    }
                                                                } else { 
                                                                    jQuery(".do.action.addItem").addClass("disabled");
                                                                }
                                                             }
        });
    };


    var oAuthLogin = function(provider, callback) {
            var getCallback = function(callback) {
                return function() {
                    validateLogin(callback);
                };
            };

            var provider_full = '';
            var login_types = qoorateLang.LOGIN_TYPES;
            var login_type;
            for ( var i = 0; i < login_types.length ; i++ ) {
                login_type = login_types[ i ];
                if ( provider == login_type[0] ) {
                  provider_full = login_type[2];
                  break;
                }
            }

            var url = qoorateConfig.QOORATE_API_URI + '/oauth/' + provider_full + '/login',
                q_short_name = getValueFromClasses('shortName', jQuery('div.q_sort_wrap').attr('class'));
            $.oauthpopup({
                path: url + '?QOOID=' + $.cookie('QOOID') + '&QOOTID=' + $.cookie('QOOTID') + '&q_short_name=' + q_short_name,
                callback: getCallback(callback),
                windowOptions: 'location=0,status=0,width=800,height=400,outerWidth=800,outerHeight=400'
            });
    };

    // We send a request, success means we are logged in and we will react accordingly
    var validateLogin = function(callback) {

        var getCallback = function(callback) {
            return function(data) {
                var data_object = parseJSONresponse(data)[0];

                // SM: 20120112 - destroy any dynamic forms we may have had from another login
                jQuery('#q_ .dyn').fadeOut(250, function(){
                                            $('#q_ .dyn').html('');
                                            });

                if( data_object != null && data_object.error == 0 && 'oAuthProvider' in data_object) {
                    var oAuthProvider = data_object.oAuthProvider,
                        is_admin = data_object.is_admin,
                        $qSocl = $('#q_socl'),
                        $q_cmnt = $('#q_cmnt'),
                        $q_head_wrap = $('#q_ .q_head_wrap');

                    $qSocl.attr('class', oAuthProvider);
                    $q_cmnt.attr('class', oAuthProvider);
                    if(is_admin){
                        $q_cmnt.addClass(' admin');
                        $q_head_wrap.addClass('admin');
                    }
                    $qSocl.find('div.q_inr').attr('class', 'q_inr logged-in ' + oAuthProvider);
                    $q_head_wrap.addClass(oAuthProvider);
                    $qSocl.find('.ttl.signin').html(qoorateLang.SIGNEDIN);
                    $qSocl.find('.ttl.logoff').html('<a href="#" id="q_logoff" class="do action logoffUser">' + qoorateLang.LOGOUT + '</a>');
                    if ( callback != null )
                        callback.call();
                }
            };
        };

        var q_short_name = getValueFromClasses('shortName', $('div.q_sort_wrap').attr('class'));

        $.ajax( {
           type: 'POST',
           url: qoorateConfig.PROXY_URI,
           data: 'action=validateLogin&QOOID=' + $.cookie('QOOID') + '&QOOTID=' + $.cookie('QOOTID') + '&q_short_name=' + q_short_name,
           success: getCallback(callback),
           error: function (xhr, error) { 
                    errorMsg(0, error);
                    //$replyLink.removeClass('disabled');
           }
        });
        
    }


    // Allows comments to be requested and returned as JSON items
    // Verbose debuging for development now
    var queryComments = function(callback, parentOffset, parentCount, childCount,
                                    sortOrder, dateOrder, voteOrder,
                                    flagTypeId) {

        var getCallback = function(callback) {
            return function(data) {
                var data_object = parseJSONresponse(data)[0];
                console.log(data_object.comments);
                console.log(data_object.query);

                if ( callback != null )
                    callback.call();

            };
        };

        var q_short_name = getValueFromClasses('shortName', $('div.q_sort_wrap').attr('class')),
            location = $('#q_').attr('class');


        var _query = Array();
        _query.push({ "name":"action",
                        "value":"queryComments"});
        _query.push({ "name":"QOOID",
                        "value":$.cookie('QOOID')});
        _query.push({ "name":"QOOTID",
                        "value":$.cookie('QOOTID')});
        _query.push({ "name":"q_short_name",
                        "value": q_short_name});
        _query.push({ "name":"location",
                        "value": location});
        if (parentOffset)
            _query.push({ "name":"parentOffset",
                            "value": parentOffset});
        if (parentCount)
            _query.push({ "name":"parentCount",
                            "value": parentCount});
        if (childCount)
            _query.push({ "name":"childCount",
                            "value": childCount});
        if (sortOrder)
            _query.push({ "name":"sortOrder",
                            "value": sortOrder});
        if (dateOrder)
            _query.push({ "name":"dateOrder",
                            "value": dateOrder});
        if (voteOrder)
            _query.push({ "name":"voteOrder",
                            "value": voteOrder});
        if (flagTypeId)
            _query.push({ "name":"flagTypeId",
                            "value": flagTypeId});

        $.ajax( {
           type: 'POST',
           url: qoorateConfig.PROXY_URI,
           data: _query,
           success: getCallback(callback),
           error: function (xhr, error) { 
                    errorMsg(0, error);
           }
        });
        
    }
    // uncomment to see values returned
    // 1 = flagType in this example
    // queryComments(null, null, null, null, null, null, null, 1);
    // queryComments();

    // SM: 20120109 - This really should be more robust, but we do have server side checks too
    var isLoggedIn = function() {
        return $("#q_logoff").length > 0;
    }

    var parseJSONresponse = function(data) {
        if ( data == null )
            return [null, null];

        if (data instanceof Object)
            return [data, data.content]

        if ( data[0] != '{' ) {
            data = data.split('\r\n\r\n');
            if( data.length > 1) {
                data =  data[1];
            } else {
                data = data[0];
            }
        }
                                                                                                                                                                                         // SM: 20111219 - should be a JSON response now                                     
        var data_object = null;
        if( data.charAt(0) == '{' ) {
            data_object = $.parseJSON(data);
            data = urldecode(data_object.content);
        }
        
        return [data_object, data];
                
    }

    /***************************************************
     * Wire up our events (called at end of init)
     ***************************************************/
    var wireEvents = function() {
        
       var $document = $(document);

       $document.delegate("input", "focus blur", function(event) {
            // SM: 20111214 - Now attach preVal to input element for pretext hint
            var $this = $(this);
            var preVal = $this.data('preVal');
    
            if (event.type == 'focus') {
                if ( $preVal != null && $this.val() == preVal)
                    $this.val('');
            } else if (event.type == 'blur') {
                if (preVal != null && $this.val() == '') {
                    $this.val(preVal);
                }
            }
        }); 
    
       $document.delegate("input.is_anonymous", "click", function(event) {
            // SM: 20111214 - Now attach preVal to input element for pretext hint
            var $this = $(this),
                $parent = $this.parent(),
                $is_anonymous_label = $parent.find('label[for="is_anonymous"]'),
                $nickname_label = $parent.find('label[for="nickname"]'),
                $nickname = $parent.find('input.nickname');
            
            if($this.is(':checked')){
                // display our textbox for the nickname
                $nickname.css('display', 'inline');
                $nickname_label.css('display', 'inline');
                $is_anonymous_label.css('display', 'none');
            }else{
                // make our input hidden our textbox for the nickname
                $nickname.css('display', 'none');
                $nickname_label.css('display', 'none');
                $is_anonymous_label.css('display', 'inline');
            }
    
        }); 
    
        $document.delegate(".q_item div.dyn","hover", function(e) {
    
            if( e.type === 'mouseenter' ) 
                $(e.currentTarget).show();
            else {
                // SM: 20111214 - No longer expected behavior
                // Should we add a cancel button instead?
                //$(e.currentTarget).slideUp('250');
            }
    
        });

        // Auto load on scroll behavior optional via conf
        if (qoorateConfig.AUTO_SCROLL > 0) {
            $document.scroll( function(e) {
                // see if we need to load more items
                var $more_link = $(".more_link_all");
                if($more_link.length > 0) {

                    var moreTop = $more_link.offset().top,
                        scrollY = Math.max( (window.scrollY?window.scrollY:0), 
                                            (document.body.scrollTop?document.body.scrollTop:0), 
                                            (document.body.parentNode.scrollTop?document.body.parentNode.scrollTop:0) ),
                        w_height = window.innerHeight,
                        scroll_diff = (moreTop - scrollY - w_height);
        
                    console.log("scroll:" + scroll_diff);
        
                    if (scroll_diff < 1000) {
                        $more_link.find('a').click();
                    }
                }
            });
        }    
        /*$('input').live('focus', function() {
            $(this).val('');
            });
    
        $('input').live('blur', function() {
            switch($(this).attr('id')) {
                case 'replyLink':
                    $(this*/
    
        //$.ajaxSetup({ cache: false });
    
        // SM: 20111214 - Added for keypress behavior
        $document.delegate('input',"keyup",function(event) {
            var $this = $(this);
            if ( $this.hasClass( 'action' ) ) {
                if ( $this.hasClass( 'replyLink' ) ) {
                    validateReplyLink( $this );
               }
            }
        });
    
        $document.delegate('textarea',"keyup",function(event) {
            var $this = $(this);
            textareaValidateAction($this);

            var $thisParent = $this.parents('.dyn'),
                charCount = $thisParent.find('.inputLength').text(),
                maxLength = $this.data("maxLength"),
                $inputVal = $thisParent.find('input').val(),
                $attachLink = $thisParent.find('a.attachLink');

    
            // MB: 20110103 - allow post w/out link thumbnail BEGIN
    
            if(($inputVal != '') && ($inputVal != qoorateLang.LINK) && (charCount >= 0) && (!$attachLink.hasClass('disabled'))) { 
                $thisParent.find('a.addItem').removeClass('disabled');
            } else if ( $attachLink.length > 0 ) {
                $thisParent.find('a.addItem').addClass('disabled');
            }
            // MB: 20110103 - allow post w/out link thumbnail END
        });
    
    
        /*$document.delegate('.q_sort_select',"change",function(event) {
    
            var $sortCurrVal = $('.q_sort_select option:selected');
            var $sortInput = $('#q_sort_by');
            var _q_short_name = getValueFromClasses('q_short_name', $('div.q_sort_wrap').attr('class'));
            if ($sortCurrVal.val() != $sortInput.val()){
                $sortInput.val($sortCurrVal.val());
                $('.q_sort_select').attr('disabled', 'disabled');
                var _query = $('#q_sort_by').serializeArray();
                _query.push({ "name":"action",  "value":"sortContribs"});
                _query.push({ "name":"page",    "value":page_md5});
                _query.push({ "name":"q_short_name",    "value":_q_short_name});
    
                $.ajax( {
                    type: 'POST',
                    url: qoorateConfig.PROXY_URI,
                    data: _query,
                    success: handleResponse('', _q_short_name, '', '', 'sortContribs','', page_md5),
                    error: function (xhr, error) { 
                        errorMsg(0, error);
                        $('.q_sort_select').removeAttr('disabled');
                    },
                    complete: function() {
                        $('.q_sort_select').removeAttr('disabled');
                    } 
                });
    
                }
            });*/
    
        $document.delegate('a',"click",function(event) {
    
            $this = $(this);
            
            $overlay = $('#q_overlay_content');
            // if our overlay is visible, ignore everything except the overlay buttons
            if ( $('#q_overlay_content').css('display') != 'none' ) {
                if ($this.parents('#q_overlay_content').length == 0 ) {
                    event.preventDefault();
                }
                return false;
            }

            // SM: 20111214 - make sure to respect disabled links
            if( $this.hasClass( "disabled" ) ) {
                event.preventDefault();
                return false;
            }

            // SM: 20120109 - Moved from own event handler
            if( $this.attr('id') == 'q_connect_tw' ){
                oAuthLogin('tw');
                event.preventDefault();
                return false;
            }
    
            // SM: 20120109 - Moved from own event handler
            if( $this.attr('id') == 'q_connect_fb' ) {
                oAuthLogin('fb');
                event.preventDefault();
                return false;
            }
    
            // SM: 20120109 - Moved from own event handler
            if( $this.attr('id') == 'q_connect_gp' ) {
                oAuthLogin('gp');
                event.preventDefault();
                return false;
            }
    
            // SM: 20120103
            // Remove our link
            if ( $this.hasClass( 'remove_link' ) ) {
                // restore the original input element
                restoreContent( $('.contribUI_Wrap'), 0);
                $('.addItem').addClass("disabled");
                return false;
            }

            // Show sort drop down
            if ( $this.hasClass('q_sort_button') ) {
                $('#q_sort_list').css('visibility', 'visible');
                scrollToObject($('#q_sort_list'));
                return false;
            }

            // Toggle our comments (grid theme only right now)
            if ( $this.hasClass('toggleReply') ) {
                if ( $this.hasClass('expand') ) {
                    $this.closest('.q_item.lv-1').addClass('active');
                    $this.removeClass('expand');
                    $this.addClass('contract');
                    $this.find('span').html(qoorateLang.TOGGLE_OFF);
                } else {
                    $this.closest('.q_item.lv-1').removeClass('active');
                    $this.removeClass('contract');
                    $this.addClass('expand');
                    $this.find('span').html(qoorateLang.TOGGLE_ON);
                }
                position();
                return false;
            }

            //GD: 20111218 check if its the
            var allClasses = $this.attr('class');
            var allClassesArray = allClasses.split(" ");
            var block_class = ($this.parents('.q_item:first').length > 0) ? $this.parents('.q_item:first') : $this.parents('.dyn');
    
            if(allClassesArray[0] == 'do') {
    
                if(allClassesArray[1] == 'view') {
                    $('.q_item').toggleClass('vi-l').toggleClass('vi-n');
                    return false;
                }
                var $attached_item = $this.parents('.q_item:first'),
                    is_child = $attached_item.hasClass('c');

                if(allClassesArray[1] == 'x') {
                  var $dynForm = $this.parents('.dyn:first'),
                    $p = $dynForm.parent(),
                    $rb = $p.find('.active'),
                    $pi = $dynForm.closest('.q_item.lv-1');
                    
                  if(is_child) {
                    $dynForm.hide();
                    $p.removeClass('active');
                    $rb.removeClass('active');
                    $rb.parent().removeClass('active');
                  }else{
                    $dynForm.hide();
                    var item_id = $dynForm.attr('class').split(' ')[1];
                    $reply_button = $('.' + item_id + '.do.makeForm.reply span:first');
                    $reply_button.html(qoorateLang.REPLY_BUTTON)
                    childToggleControls($reply_button);
                    // No longer hide children on form close
                    //$pi.removeClass('active');
                    $p.removeClass('active');
                    $rb.removeClass('active');
                    $rb.parent().removeClass('active');

                    var o = $pi.find('q_item.c');
                    jQuery.each(o, function(i, val) {
                      $dynForm = $this.parents('.dyn:first');
                      $p = $dynForm.parent();
                      $rb = $p.find('.active');
    
                      $dynForm.hide();
                      $dynForm.closest('.q_item.lv-1').removeClass('active');
                      $p.removeClass('active');
                      $rb.removeClass('active');
                      $rb.parent().removeClass('active');
                    });
    
                  }
                  position();
                  return false;
                }

                var target_function = allClassesArray[2];
                var target_id = allClassesArray[3];
                // we won't have an id for logoff
                var target_itemArray = [];
                if( target_id )
                    target_itemArray = target_id.split("-");

                var target_item_parent = null;
                var target_q_short_name = null;

                if(target_itemArray.length > 1) { 
                    target_q_short_name = target_itemArray[0];
                    target_item = target_itemArray[1];
                } else { 
                    target_q_short_name = target_id;
                    target_item = null;
                }
                  //GD 20111218 Handle Get More Children 

    
                if(allClassesArray[1] == 'makeForm') {
                    var form_type = allClassesArray[2];

                    // SM: 20111221 - Check to make sure we are logged in
                    // SM: 20120109 - Moved here so we can add the doPost as a callback for succesfull login
                    if ( !isLoggedIn() ) {

                        var getDoMakeForm = function( target_q_short_name, target_item, target_id, form_type ,block_class ) {
                            return function() {
                                doMakeForm( target_q_short_name, target_item, target_id, form_type ,block_class);
                            }
                        };

                        authError( 401, qoorateLang.SIGNIN_TO_CONTRIBUTE, getDoMakeForm( target_q_short_name, target_item, target_id, form_type ,block_class ) );

                        return false;
                    }

                    doMakeForm( target_q_short_name, target_item, target_id, form_type ,block_class );
                    //if( form_type == 'replyTopic' ) $('div.dyn').animate({'min-height' : 170 }, 'fast'); 
                    return false;
                }
    
                if(allClassesArray[1] == 'action') {
                    var post_action = allClassesArray[2]; //??? is this redundant this value is already target function ???
                    if (target_function == 'getMoreChildren') { 
                      var $parentNum = get_class_element($this, -1);
                      var parentId = $parentNum.split('-')[1];
                     target_item = parentId;
                     target_id = target_q_short_name+'-'+parentId;
                    }
                    else if (target_function == 'getMore') {
                      target_id = get_class_element($this, -1);
                    } 
                    else if (target_function == 'sort') {
                      // Remove the drop down and set hidden input value
                      $('#q_sort_list').css('visibility', 'hidden');
                      $('a.do.action.sort.disabled').removeClass('disabled');
                      $('#q_sort_by').val(  getValueFromClasses( 'order', $this.attr('class') ) );
                    }
                    // SM: 20111221 - Check to make sure we are logged in
                    // SM: 20120109 - Moved here so we can add the doPost as a callback for succesfull login
                    // We really shoul dcatch this when we vreate the form, but place it here too just in case
                    if (  !$this.hasClass('sort') && !$this.hasClass('getMore') && 
                          !$this.hasClass('getMoreChildren') && !$this.hasClass('upVote') && 
                          !$this.hasClass('downVote') && !isLoggedIn() 
                       ) {
                        var getDoPost = function( $source, target_q_short_name, target_item, target_id, post_action, block_class, location_md5) {
                            return function() {
                                $source.addClass('disabled');
                                doPost( $source, target_q_short_name, target_item, target_id, post_action, block_class, location_md5 );
                            }
                        };
                        authError( 401, qoorateLang.SIGNIN_TO_CONTRIBUTE, getDoPost( $this, target_q_short_name, target_item, target_id, post_action, block_class, location_md5 ) );
                        return false;
                    }

                    $this.addClass('disabled');
                    // SM: 20111229 - Added source as first parameter
                    doPost($this, target_q_short_name,target_item,target_id,post_action,block_class,location_md5);
                    return false;
                }
    
            }
    
            if(allClassesArray[0] == 'q_toggle') {
                //console.log($('div.' + allClassesArray[3]));
                //$('div.' + allClassesArray[2]).toggleSlide();
                //console.log($('div.' + allClassesArray[3]));
                var parId = get_class_element(block_class, -1);
                // SM:20120111 - Its not last if we are an only child
                if ( parId == 'l') {
                    parId = get_class_element(block_class, 4);
                }

                $('li.'+parId+':gt(0)').slideToggle();
                $(this).toggleClass('toggled');
                event.preventDefault();
                return false;
            }

            // SM: 20111219 - needed now that content is being passed in JSON field
            // MB : 20111231 - deactivate user link but keep link for future purposes
            $('a.q_parent').click(function(e) {
                e.preventDefault();
            });

            window.resize( dynamicResize() );
    
            /*if($(e.target).is('a.toggle')) {
            $('div.'+allClassesArray[1]).toggle();
            }
            if($(e.target).is('a.close')) {
            $(e.target).parent().toggle();
            }
    
            if($(e.target).is('a#authenticate')) {
    
            authenticate();
    
            }*/
    
        });
    }; // end wireEvents


    var skyscraper_wireEvents_pre = function() {
        
    }; // end skyscraper_wireEvents_pre
    var skyscraper_wireEvents_post = function() {
        
    }; // end skyscraper_wireEvents_post

    var grid_wireEvents_pre = function() {
        
    }; // end grid_wireEvents_pre

    var grid_wireEvents_post = function() {
        
    }; // end grid_wireEvents_post
    

    var skyscraper_ready = function() {
        
    }; // end skyscraper_ready

    var grid_ready = function() {
        childToggleControls($('#q_ .q_item'));
    }; // end grid_ready

    var childToggleControls = function($scope, $reply_count){
        var $replycount = $scope.find(".replycount");
        $replycount.each(function(){
                $this = $(this);
                if($reply_count)
                    $this.html($reply_count)
                if ($this.html() > 0){
                    if($replycount.parents('.q_item').find('.c').is(':visible')){
                        $this.closest('.inner').find('.toggleReply span').html(qoorateLang.TOGGLE_OFF);
                        $this.removeClass('expand');
                        $this.addClass('contract');
                    } else {
                        $this.closest('.inner').find('.toggleReply span').html(qoorateLang.TOGGLE_ON);
                        $this.removeClass('contract');
                        $this.addClass('expand');
                    }
                } else {
                    if($replycount.parents('.q_item').find('.c').is(':visible')){
                        $this.closest('.inner').find('.toggleReply span').html(qoorateLang.TOGGLE_OFF);
                        $this.removeClass('expand');
                        $this.addClass('contract');
                    }
                }
            }
        );
    };
    var grid_dynamicResize_pre = function() {
        grid_position();
        grid_height();
        return;
    }; // end grid_dynamicResize_pre

    var position = function() {
        var ret = call_theme_function('position') 
        rescaleImages();
        grid_height();        
        return ret;
    };

    var col_width = 600;

    var grid_position = function() {

        var c = $('#q_cmnt_contents'),
            o = $('#q_cmnt_contents .q_item.lv-1'),
            width = 600,
            cols = qoorateConfig.GRID_COLUMNS,
            col_trim = qoorateConfig.GRID_COLUMN_TRIM,
            row_trim = qoorateConfig.GRID_ROW_TRIM,
            col = 0,
            row = 0,
            c_coord = $('#q_cmnt_contents').position(),
            o_top_start = c_coord.top + 15,
            o_left_start = c_coord.left,
            o_top = 0,
            o_left = 0,
            c_top = 0,
            lastrowheights = new Array(cols),
            col_width = (width / cols) - col_trim + (col_trim/cols);
        
            
            jQuery.each(o, function(i, val) {
                val = $(val);
                if (i > cols - 1) {
                    // changed to always place in shortest column
                    //o_top = lastrowheights[col][0] + lastrowheights[col][1];
                    o_top = 0;
                    o_left = 0;
                    col = 0;
                    for (var x = 0; x < cols; x++) {
                        c_top = lastrowheights[x][0] + lastrowheights[x][1];  
                        if( o_top == 0 || o_top >= c_top){
                            col = x;
                            o_top = c_top;
                        }
                    }
                } else {
                    col = i;
                }
                o_left = col * (col_width + col_trim);
                val.css("top", o_top + "px");
                val.css("left", o_left + "px");
                val.css("width", col_width + "px");
                val.css("position", "absolute");

                // remove our row and col indexes
                val.removeClass (function (index, css) {
                    return (css.match (/\bcol-\S+/g) || []).join(' ');
                });
                
                //val.removeClass (function (index, css) {
                //    return (css.match (/\brow-\S+/g) || []).join(' ');
                //});

                // re-create our row/column indexes
                val.addClass("col-" + col);
                //val.addClass("row-" + row);
                lastrowheights[col] = [o_top, val.height() + row_trim];
                //col++;
                //if (col >= cols) {
                //    col = 0;
                //    row++;
                //    o_left = 0;
                //} else {
                //    o_left += (col_width + col_trim);
                //}        
            });

            //grid_height();

            // position our more link
            // get our last row and find the item that goes to the end
            var bottom = 0, b=0;
            for(var y=0; y<cols; y++){
                var o = lastrowheights[lastrowheights.length - y - 1];
                b = o[0] + o[1];
                if(b > bottom) {
                    bottom = b;
                }
            }
            o_top = bottom;
            val = $(".more_link_all")
            val.css("top", o_top + "px");
            val.css("left", "0px");
            val.css("width", ((col_width * cols) + (col_trim * cols)) + "px");
            val.css("position", "absolute");
            return;
    }; // end grid_position

    var grid_height = function() {
        var $c = $('#q_cmnt_contents'),
            $o = $c.find('.q_item.lv-1'),
            $more_link = $c.find(".more_link_all"),
            myheight = 0;

        if ($more_link.length==1) {
            myheight = $more_link.position().top + $more_link.height() + 15; 
        }else{
            jQuery.each($o, function(i, val) { 
                var $val = $(val);
                height = $val.position().top + $val.height() + 15; 
                if (height > myheight){
                    myheight = height;
                }
                console.log(i + ". myheight now: " + myheight);
            });
            console.log("myheight final: " + myheight);
        }
        if(myheight > 0){
            $c.height(myheight);
        }
    };
    /*!
    * jQuery OAuth via popup window plugin
    *
    * @author Nobu Funaki @zuzara
    *
    * Dual licensed under the MIT and GPL licenses:
    http://www.opensource.org/licenses/mit-license.php
    * http://www.gnu.org/licenses/gpl.html
    */
    (function($) {
        $.oauthpopup = function(options)
        {
            if (!options || !options.path) {
                throw new Error("options.path must not be empty");
            }
            $.extend({
                windowName: 'oauthWindow' // should not include space for IE
                , windowOptions: 'location=0,status=0,width=800,height=400,outerWidth=800,outerHeight=400'
                , callback: function() { window.location.reload(); }
            }, options);

            var that = this;

            var getIntervalFunction = function( options, that ) {
                return function() {
                    if ( that.oauthWindow.closed == null || 
                         that.oauthWindow.closed ){
                        window.clearInterval(that.oauthInterval);
                        options.callback();
                    }
                };
            }
 
            that.oauthWindow = window.open(options.path, options.windowName, options.windowOptions);
            that.oauthInterval = window.setInterval(getIntervalFunction(options, that), 1000);
           
        };
    })(jQuery);
    
    // Get us started!
    init();
        
    /*mgb quick edits*/
    $('.replyLink textarea')


});
