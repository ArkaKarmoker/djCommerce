/* CKEditor 5 Integration for Product Specification in Django Admin */
document.addEventListener('DOMContentLoaded', function () {
    const descField = document.querySelector('#id_description');
    if (descField && typeof ClassicEditor !== 'undefined' && !descField.classList.contains('ckeditor-attached')) {
        descField.classList.add('ckeditor-attached');
        ClassicEditor
            .create(descField, {
                toolbar: [
                    'heading', '|',
                    'bold', 'italic', 'underline', 'strikethrough', '|',
                    'bulletedList', 'numberedList', '|',
                    'insertTable', '|',
                    'link', 'blockQuote', '|',
                    'undo', 'redo'
                ],
                table: {
                    contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells']
                }
            })
            .then(editor => {
                editor.model.document.on('change:data', () => {
                    descField.value = editor.getData();
                });
                if (descField.form) {
                    descField.form.addEventListener('submit', () => {
                        descField.value = editor.getData();
                    });
                }
            })
            .catch(err => {
                console.error('Failed to initialize CKEditor for Specification:', err);
            });
    }
});
