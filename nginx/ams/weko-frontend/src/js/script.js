window.onload = function() {
/**
 * modal
 */
const modalBtn = document.querySelectorAll("button.btn-modal");
modalBtn.forEach((btn) => {
    btn.addEventListener("click", () => {
    if (btn.dataset?.target) {
      document.getElementById("modal" + btn.dataset?.target).showModal();
      return false;
    }
  });
});

/**
 * indexTree bar
 */
function fixedMenu() {
  var IndexTree = document.getElementById("IndexTree");
  var IndexTreeHeight = IndexTree?.offsetHeight;
  if (window.scrollY >= IndexTreeHeight) {
    IndexTree.classList.add("scroll");
  } else {
    IndexTree.classList.remove("scroll");
  }
}

window.addEventListener("load", fixedMenu);
window.addEventListener("resize", fixedMenu);
window.addEventListener("scroll", fixedMenu);

/**
 * indexTree modal
 */
var scrollTop;
function showModal(target) {
  scrollTop = window.scrollY;
  document.getElementById(target).showModal();
  document.getElementById("IndexTree").classList.add("show");
}

function closeModal(target) {
  document.getElementById(target).close();
  document.getElementById("IndexTree").classList.remove("show");
}



document.querySelector(".btn-lang").addEventListener("click", () => {
  document.querySelector(".link-lang").classList.toggle("hidden");
});


/**
 * faq
 */
document.addEventListener('DOMContentLoaded', () => {
  // anker
  let elms = document.querySelectorAll('.anker');
    elms?.forEach((elm) => { 
      elm.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(e.currentTarget.getAttribute('href'));
        if (target) {
          target.scrollIntoView({
            behavior: "smooth",
          });
        }
      })
    })

  // pageTop
  let pagetopBtn = document.getElementById("page-top");
  pagetopBtn?.addEventListener("click", (e) => {
    window.scrollTo({top: 0, behavior: 'smooth'})
    return false;
  });
})
}