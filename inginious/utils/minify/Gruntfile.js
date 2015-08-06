module.exports = function(grunt)
{
    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        concat: {
            options: {
                // define a string to put between each file in the concatenated output
                separator: '\n /* --- */ \n'
            },
            dist: {
                files: {
                    '../../frontend/webapp/static/js/all-minified.js': [
                        '../../frontend/common/static/js/libs/jquery.min.js',
                        '../../frontend/common/static/js/libs/jquery.form.min.js',
                        '../../frontend/common/static/js/libs/bootstrap.min.js',
                        '../../frontend/common/static/js/libs/bootstrap-datetimepicker.min.js',
                        '../../frontend/common/static/js/libs/checked-list-group.js',
                        '../../frontend/common/static/js/codemirror/codemirror.js',
                        '../../frontend/common/static/js/common.js',
                        '../../frontend/common/static/js/task.js',
                        '../../frontend/webapp/static/js/jquery-sortable.min.js',
                        '../../frontend/webapp/static/js/webapp.js',
                        '../../frontend/webapp/static/js/studio.js',
			'../../frontend/webapp/static/js/classrooms.js'
                    ],
                    '../../frontend/lti/static/js/all-minified.js': [
                        '../../frontend/common/static/js/libs/jquery.min.js',
                        '../../frontend/common/static/js/libs/jquery.form.min.js',
                        '../../frontend/common/static/js/libs/bootstrap.min.js',
                        '../../frontend/common/static/js/libs/bootstrap-datetimepicker.min.js',
                        '../../frontend/common/static/js/libs/checked-list-group.js',
                        '../../frontend/common/static/js/codemirror/codemirror.js',
                        '../../frontend/common/static/js/common.js',
                        '../../frontend/common/static/js/task.js',
                        '../../frontend/lti/static/js/lti.js'
                    ]
                }
            }
        },
        uglify: {
            options: {
                compress: true
            },
            dist: {
                files: {
                    '../../frontend/webapp/static/js/all-minified.js': ['../../frontend/webapp/static/js/all-minified.js'],
                    '../../frontend/lti/static/js/all-minified.js': ['../../frontend/lti/static/js/all-minified.js']
                }
            }
        }
    });

    // Load the plugin that provides the "uglify" task.
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-compress');

    // Default task(s).
    grunt.registerTask('default', ['concat', 'uglify']);
};
