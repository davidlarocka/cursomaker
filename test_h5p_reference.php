<?php

define('CLI_SCRIPT', true);

require '/var/www/html/aulavirtual/config.php';

global $DB;
global $USER;

$USER = $DB->get_record(
    'user',
    ['id' => 8],
    '*',
    MUST_EXIST
);

$contentid = 13;
$repositoryid = 2;

// Usuario del agente.
$userid = 8;

// Obtener el contenido del Content Bank.
$contentrecord = $DB->get_record(
    'contentbank_content',
    ['id' => $contentid],
    '*',
    MUST_EXIST
);

// Obtener el contexto donde vive el contenido.
$contentcontext = \context::instance_by_id(
    $contentrecord->contextid,
    MUST_EXIST
);

// Obtener el archivo real del Content Bank.
$managerclass = '\\' . $contentrecord->contenttype . '\\content';

if (!class_exists($managerclass)) {
    throw new \moodle_exception(
        'No existe la clase de contenido: ' . $managerclass
    );
}

$content = new $managerclass($contentrecord);

$file = $content->get_file();

if (!$file) {
    throw new \moodle_exception(
        'El contenido no tiene archivo asociado.'
    );
}

// Construir exactamente el source que usa Moodle.
$params = [
    'contextid' => $file->get_contextid(),
    'component' => $file->get_component(),
    'filearea'  => $file->get_filearea(),
    'itemid'    => $file->get_itemid(),
    'filepath'  => $file->get_filepath(),
    'filename'  => $file->get_filename(),
];

$reference = base64_encode(
    json_encode($params)
);

// Crear draft item.
$draftitemid = file_get_unused_draft_itemid();

// Archivo destino de la referencia.
$filerecord = [
    'contextid' => \context_user::instance($userid)->id,
    'component' => 'user',
    'filearea'  => 'draft',
    'itemid'    => $draftitemid,
    'filepath'  => '/',
    'filename'  => $file->get_filename(),
    'userid'    => $userid,
];

// Crear referencia.
$fs = get_file_storage();

$storedfile = $fs->create_file_from_reference(
    $filerecord,
    $repositoryid,
    $reference
);

echo "=== REFERENCIA H5P ===\n";
echo "Content ID: {$contentid}\n";
echo "Repository ID: {$repositoryid}\n";
echo "Draft Item ID: {$draftitemid}\n";
echo "Filename: {$storedfile->get_filename()}\n";
echo "Context ID: {$storedfile->get_contextid()}\n";
echo "Component: {$storedfile->get_component()}\n";
echo "File area: {$storedfile->get_filearea()}\n";
echo "Item ID: {$storedfile->get_itemid()}\n";
echo "Is external: ";
var_dump($storedfile->is_external_file());
echo "Reference: ";
var_dump($storedfile->get_reference());