
#include "opengl_renderer.h"
#include <GL/gl.h>
#include <GL/glu.h>
#include <cstring>
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static const char* last_error = nullptr;

void set_error(const char* msg) {
    last_error = msg;
}

void draw_cube(float size) {
    float h = size / 2.0f;
    glBegin(GL_QUADS);
    glVertex3f(-h, -h, -h); glVertex3f(h, -h, -h); glVertex3f(h, h, -h); glVertex3f(-h, h, -h);
    glVertex3f(-h, -h, h); glVertex3f(h, -h, h); glVertex3f(h, h, h); glVertex3f(-h, h, h);
    glVertex3f(-h, -h, -h); glVertex3f(-h, h, -h); glVertex3f(-h, h, h); glVertex3f(-h, -h, h);
    glVertex3f(h, -h, -h); glVertex3f(h, h, -h); glVertex3f(h, h, h); glVertex3f(h, -h, h);
    glVertex3f(-h, -h, -h); glVertex3f(-h, -h, h); glVertex3f(h, -h, h); glVertex3f(h, -h, -h);
    glVertex3f(-h, h, -h); glVertex3f(-h, h, h); glVertex3f(h, h, h); glVertex3f(h, h, -h);
    glEnd();
}

void draw_sphere(float radius, int slices, int stacks) {
    for (int i = 0; i < stacks; i++) {
        float lat0 = M_PI * (-0.5f + (float)(i) / stacks);
        float lat1 = M_PI * (-0.5f + (float)(i + 1) / stacks);
        float z0 = sin(lat0);
        float z1 = sin(lat1);
        float r0 = cos(lat0);
        float r1 = cos(lat1);
        
        glBegin(GL_QUAD_STRIP);
        for (int j = 0; j <= slices; j++) {
            float lng = 2 * M_PI * (float)(j - 1) / slices;
            float x = cos(lng);
            float y = sin(lng);
            glVertex3f(r0 * x, r0 * y, z0);
            glVertex3f(r1 * x, r1 * y, z1);
        }
        glEnd();
    }
}

void draw_cone(float base_radius, float height, int slices) {
    float half_height = height / 2.0f;
    glBegin(GL_TRIANGLES);
    for (int i = 0; i < slices; i++) {
        float angle1 = 2 * M_PI * (float)i / slices;
        float angle2 = 2 * M_PI * (float)(i + 1) / slices;
        glVertex3f(0, half_height, 0);
        glVertex3f(base_radius * cos(angle1), -half_height, base_radius * sin(angle1));
        glVertex3f(base_radius * cos(angle2), -half_height, base_radius * sin(angle2));
    }
    glEnd();
}

extern "C" {

RENDERER_API const char* get_last_error() {
    return last_error;
}

RENDERER_API void init_renderer(int width, int height) {
    set_error(nullptr);
    glViewport(0, 0, width, height);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(60.0f, (float)width / height, 0.1f, 1000.0f);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_LIGHTING);
    glEnable(GL_LIGHT0);
    glEnable(GL_COLOR_MATERIAL);
}

RENDERER_API void render_terrain(float player_x, float player_y, float player_z, float visible_range, float block_size, float height) {
    set_error(nullptr);
    glDisable(GL_LIGHTING);
    
    int range = (int)(visible_range / block_size);
    for (int dx = -range; dx <= range; dx++) {
        for (int dz = -range; dz <= range; dz++) {
            float x = player_x + dx * block_size;
            float z = player_z + dz * block_size;
            
            float dist = sqrt((float)(dx*dx + dz*dz)) * block_size;
            if (dist > visible_range) continue;
            
            float h = height;
            glColor3f(0.3f, 0.6f, 0.3f);
            glBegin(GL_QUADS);
            glVertex3f(x, 0, z);
            glVertex3f(x + block_size, 0, z);
            glVertex3f(x + block_size, 0, z + block_size);
            glVertex3f(x, 0, z + block_size);
            glEnd();
            
            glColor3f(0.5f, 0.7f, 0.5f);
            glBegin(GL_QUADS);
            glVertex3f(x, h, z);
            glVertex3f(x + block_size, h, z);
            glVertex3f(x + block_size, h, z + block_size);
            glVertex3f(x, h, z + block_size);
            glEnd();
            
            glColor3f(0.4f, 0.55f, 0.4f);
            glBegin(GL_QUADS);
            glVertex3f(x, 0, z);
            glVertex3f(x + block_size, 0, z);
            glVertex3f(x + block_size, h, z);
            glVertex3f(x, h, z);
            glEnd();
        }
    }
    glEnable(GL_LIGHTING);
}

RENDERER_API void render_projectiles(ProjectileData* projectiles, int count) {
    set_error(nullptr);
    glDisable(GL_LIGHTING);
    for (int i = 0; i < count; i++) {
        glColor3f(projectiles[i].r, projectiles[i].g, projectiles[i].b);
        glPushMatrix();
        glTranslatef(projectiles[i].x, projectiles[i].y, projectiles[i].z);
        draw_sphere(projectiles[i].radius, 8, 8);
        glPopMatrix();
    }
    glEnable(GL_LIGHTING);
}

RENDERER_API void render_pickups(PickupData* pickups, int count) {
    set_error(nullptr);
    glDisable(GL_LIGHTING);
    for (int i = 0; i < count; i++) {
        glColor3f(pickups[i].r, pickups[i].g, pickups[i].b);
        glPushMatrix();
        glTranslatef(pickups[i].x, pickups[i].y, pickups[i].z);
        draw_cube(pickups[i].size);
        glPopMatrix();
    }
    glEnable(GL_LIGHTING);
}

RENDERER_API void render_tech_blocks(TechBlockData* blocks, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glColor3f(0.2f, 0.4f, 0.8f);
        glPushMatrix();
        glTranslatef(blocks[i].x, blocks[i].y, blocks[i].z);
        draw_cube(blocks[i].size);
        glPopMatrix();
    }
}

RENDERER_API void render_trees(TreeData* trees, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glPushMatrix();
        glTranslatef(trees[i].x, trees[i].base_height / 2, trees[i].z);
        
        glColor3f(0.3f, 0.2f, 0.1f);
        glScalef(0.3f, trees[i].base_height, 0.3f);
        draw_cube(1.0f);
        
        glTranslatef(0, trees[i].base_height / 2 + trees[i].height / 2, 0);
        glColor3f(0.2f, 0.6f, 0.2f);
        glScalef(trees[i].width / 0.3f, trees[i].height / trees[i].base_height, trees[i].width / 0.3f);
        draw_sphere(0.5f, 8, 8);
        glPopMatrix();
    }
}

RENDERER_API void render_structures(StructureData* structures, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glColor3f(0.6f, 0.5f, 0.4f);
        glPushMatrix();
        glTranslatef(structures[i].x, structures[i].height / 2, structures[i].z);
        glScalef(structures[i].width, structures[i].height, structures[i].depth);
        draw_cube(1.0f);
        glPopMatrix();
    }
}

RENDERER_API void render_locations(LocationData* locations, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glColor3f(locations[i].r, locations[i].g, locations[i].b);
        glPushMatrix();
        glTranslatef(locations[i].x, 2.0f, locations[i].z);
        draw_cone(2.0f, 4.0f, 8);
        glPopMatrix();
    }
}

RENDERER_API void render_npcs(NPCData* npcs, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glPushMatrix();
        glTranslatef(npcs[i].x, npcs[i].y + 0.9f, npcs[i].z);
        
        glColor3f(0.6f, 0.4f, 0.2f);
        glScalef(0.4f, 1.8f, 0.4f);
        draw_cube(1.0f);
        
        glTranslatef(0, 1.0f, 0);
        glColor3f(0.8f, 0.6f, 0.4f);
        glScalef(0.7f, 0.7f, 0.7f);
        draw_sphere(0.5f, 8, 8);
        glPopMatrix();
    }
}

RENDERER_API void render_enemies(EnemyData* enemies, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glPushMatrix();
        glTranslatef(enemies[i].x, enemies[i].y + 1.0f, enemies[i].z);
        
        glColor3f(0.8f, 0.2f, 0.2f);
        glScalef(0.5f, 2.0f, 0.5f);
        draw_cube(1.0f);
        
        float health_ratio = enemies[i].current_health / enemies[i].max_health;
        glColor3f(1.0f - health_ratio, health_ratio, 0.0f);
        glBegin(GL_QUADS);
        glVertex3f(-0.5f, 1.1f, -0.3f);
        glVertex3f(-0.5f + health_ratio, 1.1f, -0.3f);
        glVertex3f(-0.5f + health_ratio, 1.15f, -0.3f);
        glVertex3f(-0.5f, 1.15f, -0.3f);
        glEnd();
        glPopMatrix();
    }
}

RENDERER_API void render_generals(GeneralData* generals, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glPushMatrix();
        glTranslatef(generals[i].x, generals[i].y + 1.1f, generals[i].z);
        
        glColor3f(0.2f, 0.3f, 0.6f);
        glScalef(0.5f, 2.2f, 0.5f);
        draw_cube(1.0f);
        
        glTranslatef(0, 1.0f, 0);
        glColor3f(0.9f, 0.7f, 0.5f);
        glScalef(0.8f, 0.8f, 0.8f);
        draw_sphere(0.5f, 8, 8);
        
        if (generals[i].has_weapon) {
            glTranslatef(0.5f, -0.5f, 0);
            glColor3f(0.7f, 0.7f, 0.7f);
            glScalef(0.1f, 1.5f, 0.1f);
            draw_cube(1.0f);
        }
        glPopMatrix();
    }
}

RENDERER_API void render_pets(PetData* pets, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glColor3f(pets[i].r, pets[i].g, pets[i].b);
        glPushMatrix();
        glTranslatef(pets[i].x, pets[i].y + pets[i].size / 2, pets[i].z);
        draw_sphere(pets[i].size / 2, 8, 8);
        glPopMatrix();
    }
}

RENDERER_API void render_player(PlayerData* player) {
    set_error(nullptr);
    if (!player) return;
    
    glPushMatrix();
    glTranslatef(player->x, player->y + 1.0f, player->z);
    
    glColor3f(0.3f, 0.5f, 0.8f);
    glScalef(0.5f, 2.0f, 0.5f);
    draw_cube(1.0f);
    
    glTranslatef(0, 1.0f, 0);
    glColor3f(0.8f, 0.6f, 0.4f);
    glScalef(0.8f, 0.8f, 0.8f);
    draw_sphere(0.5f, 8, 8);
    glPopMatrix();
}

RENDERER_API void render_followers(FollowerData* followers, int count) {
    set_error(nullptr);
    for (int i = 0; i < count; i++) {
        glColor3f(0.4f, 0.6f, 0.3f);
        glPushMatrix();
        glTranslatef(followers[i].x, followers[i].y + 0.8f, followers[i].z);
        glScalef(0.4f, 1.6f, 0.4f);
        draw_cube(1.0f);
        glPopMatrix();
    }
}

RENDERER_API void render_particles(ParticleData* particles, int count) {
    set_error(nullptr);
    glDisable(GL_LIGHTING);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    for (int i = 0; i < count; i++) {
        glColor4f(particles[i].r, particles[i].g, particles[i].b, particles[i].alpha);
        glPushMatrix();
        glTranslatef(particles[i].x, particles[i].y, particles[i].z);
        draw_sphere(particles[i].size, 8, 8);
        glPopMatrix();
    }
    
    glDisable(GL_BLEND);
    glEnable(GL_LIGHTING);
}

}
