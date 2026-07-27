(function () {
  'use strict';

  document.documentElement.classList.add('reveal-ready');

  var MAX_FILE_SIZE = 2 * 1024 * 1024;
  var body = document.body;
  var header = document.querySelector('.site-header');
  var menu = document.getElementById('mobile-menu');
  var menuOverlay = document.getElementById('menu-overlay');
  var menuToggle = document.querySelector('.menu-toggle');
  var closeMenuButton = document.querySelector('.close-menu');
  var backdrop = document.getElementById('modal-backdrop');
  var requestModal = document.getElementById('request-modal');
  var policyModal = document.getElementById('policy-modal');
  var requestForm = document.getElementById('request-form');
  var formSuccess = document.getElementById('form-success');
  var toast = document.getElementById('toast');
  var lastTrigger = null;
  var activeModal = null;
  var toastTimer = null;

  function setHeaderState() {
    header.classList.toggle('scrolled', window.scrollY > 12);
  }

  function showToast(message) {
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add('show');
    toastTimer = window.setTimeout(function () {
      toast.classList.remove('show');
    }, 4200);
  }

  function lockBody() {
    body.classList.add('no-scroll');
  }

  function unlockBody() {
    if (!menu.classList.contains('is-open') && !activeModal) {
      body.classList.remove('no-scroll');
    }
  }

  function openMenu() {
    if (activeModal) return;
    menuOverlay.hidden = false;
    menu.setAttribute('aria-hidden', 'false');
    menuToggle.setAttribute('aria-expanded', 'true');
    lockBody();
    window.requestAnimationFrame(function () {
      menuOverlay.classList.add('is-open');
      menu.classList.add('is-open');
      closeMenuButton.focus();
    });
  }

  function closeMenu(focusToggle) {
    if (!menu.classList.contains('is-open')) return;
    menuOverlay.classList.remove('is-open');
    menu.classList.remove('is-open');
    menu.setAttribute('aria-hidden', 'true');
    menuToggle.setAttribute('aria-expanded', 'false');
    window.setTimeout(function () {
      if (!menu.classList.contains('is-open')) menuOverlay.hidden = true;
    }, 320);
    unlockBody();
    if (focusToggle) menuToggle.focus();
  }

  function openModal(modal, trigger) {
    closeMenu(false);
    lastTrigger = trigger || document.activeElement;
    activeModal = modal;
    backdrop.hidden = false;
    modal.hidden = false;
    lockBody();
    window.requestAnimationFrame(function () {
      backdrop.classList.add('is-open');
      modal.classList.add('is-open');
      var autofocusTarget = modal.querySelector('input, select, textarea, button');
      if (autofocusTarget) autofocusTarget.focus();
    });
  }

  function closeModal(restoreFocus) {
    if (!activeModal) return;
    var modal = activeModal;
    modal.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    activeModal = null;
    window.setTimeout(function () {
      if (!modal.classList.contains('is-open')) modal.hidden = true;
      if (!activeModal) backdrop.hidden = true;
    }, 240);
    unlockBody();
    if (restoreFocus && lastTrigger && typeof lastTrigger.focus === 'function') lastTrigger.focus();
  }

  function setFieldError(fieldName, message) {
    var input = requestForm.elements[fieldName];
    var field = input ? input.closest('.field') : null;
    var error = requestForm.querySelector('[data-error-for="' + fieldName + '"]');
    if (field) field.classList.toggle('is-invalid', Boolean(message));
    if (input && message) input.setAttribute('aria-invalid', 'true');
    if (input && !message) input.removeAttribute('aria-invalid');
    if (error) error.textContent = message || '';
  }

  function cleanPhone(value) {
    return value.replace(/\D/g, '');
  }

  function validateField(name) {
    var value = String(requestForm.elements[name].value || '').trim();
    var message = '';
    if (name === 'name' && value.length < 2) message = 'Укажите имя — минимум 2 символа.';
    if (name === 'phone' && cleanPhone(value).length < 10) message = 'Введите телефон в понятном формате.';
    if (name === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) message = 'Введите корректный email.';
    if (name === 'service' && !value) message = 'Выберите интересующую услугу.';
    if (name === 'file') {
      var file = requestForm.elements.file.files[0];
      if (file && file.size > MAX_FILE_SIZE) message = 'Для демо-версии доступен файл до 2 МБ.';
    }
    setFieldError(name, message);
    return !message;
  }

  function formatPhone(event) {
    var digits = cleanPhone(event.target.value);
    if (!digits) return;
    if (digits.charAt(0) === '8') digits = '7' + digits.slice(1);
    if (digits.charAt(0) !== '7') digits = '7' + digits;
    var result = '+7';
    if (digits.length > 1) result += ' (' + digits.slice(1, 4);
    if (digits.length >= 5) result += ') ' + digits.slice(4, 7);
    if (digits.length >= 8) result += '-' + digits.slice(7, 9);
    if (digits.length >= 10) result += '-' + digits.slice(9, 11);
    event.target.value = result;
  }

  function updateFileLabel() {
    var file = requestForm.elements.file.files[0];
    document.getElementById('file-name').textContent = file ? file.name : 'Файл не выбран';
    validateField('file');
  }

  function resetFormState() {
    requestForm.reset();
    document.getElementById('file-name').textContent = 'Файл не выбран';
    Array.prototype.forEach.call(requestForm.querySelectorAll('.field'), function (field) { field.classList.remove('is-invalid'); });
    Array.prototype.forEach.call(requestForm.querySelectorAll('.field-error'), function (error) { error.textContent = ''; });
    formSuccess.hidden = true;
    requestForm.hidden = false;
  }

  function formSubmit(event) {
    event.preventDefault();
    var valid = ['name', 'phone', 'email', 'service', 'file'].every(validateField);
    if (!valid) {
      var invalid = requestForm.querySelector('[aria-invalid="true"]');
      if (invalid) invalid.focus();
      showToast('Проверьте поля, отмеченные красным.');
      return;
    }
    var submitButton = requestForm.querySelector('[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = 'Отправляем…';
    requestForm.hidden = true;
    formSuccess.hidden = false;
    showToast('Заявка сохранена. Спасибо!');
    requestForm.reset();
    document.getElementById('file-name').textContent = 'Файл не выбран';
    submitButton.disabled = false;
    submitButton.innerHTML = 'Отправить заявку <span class="button-arrow" aria-hidden="true">↗</span>';
  }

  function setupReveal() {
    var items = document.querySelectorAll('.reveal');
    var staggeredParents = ['service-grid', 'product-list', 'advantage-grid', 'steps-list'];

    Array.prototype.forEach.call(items, function (item) {
      var parent = item.parentElement;
      var revealIndex = 0;
      var child;

      if (!parent || staggeredParents.indexOf(parent.className) === -1) return;

      child = parent.firstElementChild;
      while (child && child !== item) {
        if (child.classList.contains('reveal')) revealIndex += 1;
        child = child.nextElementSibling;
      }

      item.style.setProperty('--reveal-delay', Math.min(revealIndex * 55, 275) + 'ms');
    });

    if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      Array.prototype.forEach.call(items, function (item) { item.classList.add('visible'); });
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.1 });
    Array.prototype.forEach.call(items, function (item) { observer.observe(item); });
  }

  function setupParallax() {
    var area = document.querySelector('[data-parallax-area]');
    if (!area || !window.matchMedia('(pointer: fine)').matches || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var cards = area.querySelectorAll('[data-parallax]');
    area.addEventListener('pointermove', function (event) {
      var rect = area.getBoundingClientRect();
      var x = (event.clientX - rect.left) / rect.width - .5;
      var y = (event.clientY - rect.top) / rect.height - .5;
      Array.prototype.forEach.call(cards, function (card) {
        var amount = Number(card.getAttribute('data-parallax'));
        card.style.translate = (x * amount) + 'px ' + (y * amount) + 'px';
      });
    });
    area.addEventListener('pointerleave', function () {
      Array.prototype.forEach.call(cards, function (card) { card.style.translate = ''; });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    setHeaderState();
    setupReveal();
    setupParallax();
    document.getElementById('current-year').textContent = new Date().getFullYear();

    window.addEventListener('scroll', setHeaderState, { passive: true });
    menuToggle.addEventListener('click', openMenu);
    closeMenuButton.addEventListener('click', function () { closeMenu(true); });
    menuOverlay.addEventListener('click', function () { closeMenu(true); });
    Array.prototype.forEach.call(document.querySelectorAll('.mobile-nav a'), function (link) {
      link.addEventListener('click', function () { closeMenu(false); });
    });

    Array.prototype.forEach.call(document.querySelectorAll('[data-open-form]'), function (button) {
      button.addEventListener('click', function () {
        var service = button.getAttribute('data-service');
        resetFormState();
        if (service) requestForm.elements.service.value = service;
        openModal(requestModal, button);
      });
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-open-policy]'), function (button) {
      button.addEventListener('click', function () { openModal(policyModal, button); });
    });
    Array.prototype.forEach.call(document.querySelectorAll('.close-modal, [data-close-modal]'), function (button) {
      button.addEventListener('click', function () { closeModal(true); });
    });
    backdrop.addEventListener('click', function () { closeModal(true); });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        if (activeModal) closeModal(true);
        else closeMenu(true);
      }
    });

    requestForm.addEventListener('submit', formSubmit);
    requestForm.elements.phone.addEventListener('input', formatPhone);
    ['name', 'phone', 'email', 'service'].forEach(function (name) {
      var eventName = name === 'service' ? 'change' : 'blur';
      requestForm.elements[name].addEventListener(eventName, function () { validateField(name); });
    });
    requestForm.elements.file.addEventListener('change', updateFileLabel);

    document.querySelector('[data-to-top]').addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
}());
