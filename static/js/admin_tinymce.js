document.addEventListener('DOMContentLoaded', function() {
    if (typeof tinymce === 'undefined') return;

    tinymce.init({
        selector: '#id_description',
        height: 480,
        menubar: 'file edit view insert format tools table help',
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'help', 'wordcount'
        ],
        toolbar: 'undo redo | blocks fontfamily fontsize | ' +
            'bold italic underline strikethrough | forecolor backcolor | alignleft aligncenter ' +
            'alignright alignjustify | bullist numlist outdent indent | ' +
            'table link image media | removeformat | code fullscreen preview',
        content_style: 'body { font-family: system-ui, -apple-system, sans-serif; font-size: 14px; line-height: 1.6; } table { border-collapse: collapse; width: 100%; } table, th, td { border: 1px solid #ddd; padding: 8px; }',
        branding: false,
        promotion: false,
        setup: function(editor) {
            editor.on('change', function() {
                editor.save();
            });
        }
    });
});
