import time
import moderngl
import numpy as np
import subprocess
import threading

def get_current_gpu_temp():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader'], 
            capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return int(result.stdout.strip())
    except Exception:
        return -1

def monitor_temp_and_progress(duration, stop_event, temp_data, task_name):
    start = time.time()
    loops = 0
    while not stop_event.is_set():
        elapsed = time.time() - start
        pct = min(100, int((elapsed / duration) * 100))
        print(f"PROGRESS: {task_name} | PCT: {pct}", flush=True)
        
        if loops % 2 == 0:
            current_temp = get_current_gpu_temp()
            if current_temp > temp_data['max_temp']:
                temp_data['max_temp'] = current_temp
        
        loops += 1
        time.sleep(0.5)

def run_real_gpu_benchmark():
    stop_event = threading.Event()
    temp_data = {'max_temp': -1}
    
    ramp_duration = 10.0
    sustain_duration = 40.0 
    total_duration = ramp_duration + sustain_duration
    
    monitor_thread = threading.Thread(
        target=monitor_temp_and_progress, 
        args=(total_duration, stop_event, temp_data, "GPU 3D Rendering Test")
    )
    monitor_thread.start()
    
    start_time = time.time()
    
    try:
        ctx = moderngl.create_context(standalone=True)
        
        prog = ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_position;
                void main() {
                    gl_Position = vec4(in_position, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                uniform int u_intensity;
                out vec4 fragColor;
                void main() {
                    vec2 p = gl_FragCoord.xy * 0.001;
                    float val = 0.0;
                    for(int i=0; i < u_intensity; i++) {
                        val += sin(p.x * float(i)) * cos(p.y * float(i));
                    }
                    fragColor = vec4(vec3(val), 1.0);
                }
            '''
        )
        
        vertices_data = np.array([
            -1.0, -1.0,  1.0, -1.0, -1.0,  1.0,
             1.0, -1.0,  1.0,  1.0, -1.0,  1.0,
        ], dtype='f4')
        
        vbo = ctx.buffer(vertices_data.tobytes())
        vao = ctx.vertex_array(prog, [(vbo, '2f', 'in_position')])
        
        fbo_size = (3840, 2160)
        tex = ctx.texture(fbo_size, 4)
        fbo = ctx.framebuffer(color_attachments=[tex])
        fbo.use()
        
        prog['u_intensity'].value = 800 
        cycle_time = 0.05
        
        loop_start = time.time()
        iterations = 0
        
        while True:
            elapsed = time.time() - loop_start
            if elapsed >= total_duration:
                break
                
            if elapsed < ramp_duration:
                target_load = elapsed / ramp_duration
            else:
                target_load = 1.0
                
            work_time = cycle_time * target_load
            sleep_time = cycle_time - work_time
            
            work_start = time.time()
            while time.time() - work_start < work_time:
                ctx.clear()
                vao.render(moderngl.TRIANGLES)
                ctx.finish()
                iterations += 1
            
            if sleep_time > 0.001:
                time.sleep(sleep_time)
                
    except Exception as e:
        print(f"ModernGL execution error: {e}")
        stop_event.set()
        monitor_thread.join()
        raise RuntimeError(f"GPU rendering benchmark could not complete: {e}") from e
        
    end_time = time.time()
    stop_event.set()
    monitor_thread.join()
    
    time_taken = end_time - start_time
    
    iterations_per_sec = iterations / max(0.1, time_taken)
    # Calibrated multiplier to output ~35k for RTX 5070
    final_score = int(iterations_per_sec * 107) 
    
    if final_score < 2000:
        final_score = 2000
    
    return final_score, time_taken

if __name__ == "__main__":
    run_real_gpu_benchmark()