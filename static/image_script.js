


function close_full_image(image){
    image.classList.add('image');
    image.classList.remove('image_full');
    image.setAttribute('onclick', 'open_full_image(this)');
}


function open_full_image(image){
  image.classList.add('image_full');
  image.classList.remove('image');
  image.setAttribute('onclick', 'close_full_image(this)');
}