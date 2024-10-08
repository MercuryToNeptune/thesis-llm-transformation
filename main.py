import preprocess as preprocess
import postprocess as postprocess
import analyze_cmake as analyze_cmake
import analyze_src_code as analyze_src_code

variant_paths = [
    'C:/Users/aatra/Desktop/2022- Deutschland/Uni Stuttgart/Sem 4/MA/code/self-cloned-variants-SPLed/blinking_light',
    'C:/Users/aatra/Desktop/2022- Deutschland/Uni Stuttgart/Sem 4/MA/code/self-cloned-variants-SPLed/color_light',
    'C:/Users/aatra/Desktop/2022- Deutschland/Uni Stuttgart/Sem 4/MA/code/self-cloned-variants-SPLed/color_light_green',
    'C:/Users/aatra/Desktop/2022- Deutschland/Uni Stuttgart/Sem 4/MA/code/self-cloned-variants-SPLed/dimmable_light',
]
spl_output = 'C:/Users/aatra/Desktop/demo_extension/spl_output'

variant_names = preprocess.extract_variant_names(variant_paths)
preprocess.create_spl_directory(variant_paths, spl_output)
preprocess.create_prompt_dirs()
print("Pre-processing complete.")

analyze_cmake.stitch_variablecmake_into_prompt()
cmake_gen_fail = analyze_cmake.create_platform_cmake()

if not cmake_gen_fail:
    print("Generation of platform build file complete.")
    src_code_gen_fail = analyze_src_code.create_platform_src_code(variant_names)
    if not cmake_gen_fail and not src_code_gen_fail:
        print("Generation of platform source-code successful.")
        postprocess.cleanup_success()
        print("Generated Platform available under 'spl_output' directory.")
        print("Post-processing complete.")
    elif not cmake_gen_fail and src_code_gen_fail:
        print("Generation of platform source-code failed.")
        postprocess.cleanup_fail()
else:
    print("Generation of platform build file not successful.")
    postprocess.cleanup_fail()



