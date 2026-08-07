#define RENDERER_EXPORTS
#include "opengl_renderer.h"
#include <GL/gl.h>
#include <GL/glu.h>
#include <cmath>
#include <cstring>
#include <vector>
#include <string>

static std::string s_error;

static void set_error(const char* msg) {
    s_error = msg;
}

const char* get_renderer_error() {
    return s_error.c_str();
}

void init_renderer(int screen_width, int screen_height) {
    set_error(nullptr);

    glEnable(GL_DEPTH_TEST);
    glEnable(GL_TEXTURE_2D);
    glEnable(GL_LIGHTING);
    glEnable(GL_LIGHT0);

    glClearColor(0.1f, 0.1f, 0.2f, 1.0f);

    float light_position[] = { 1.0f, 1.0f, 1.0f, 0.0f };
    glLightfv(GL_LIGHT0, GL_POSITION, light_position);
}

void cleanup_renderer() {
}

void render_terrain(
    float player_x, float player_y, float player_z,
    float visible_range,
    float block_size,
    float height
) {
    glDisable(GL_LIGHTING);

    int start_x = static_cast<int>((player_x - visible_range) / block_size) * static_cast<int>(block_size);
    int end_x = static_cast<int>((player_x + visible_range) / block_size) * static_cast<int>(block_size);
    int start_z = static_cast<int>((player_z - visible_range) / block_size) * static_cast<int>(block_size);
    int end_z = static_cast<int>((player_z + visible_range) / block_size) * static_cast<int>(block_size);

    for (int x = start_x; x < end_x; x += static_cast<int>(block_size)) {
        for (int z = start_z; z < end_z; z += static_cast<int>(block_size)) {
            float noise = sinf(x * 0.008f) * cosf(z * 0.008f) * 3.0f +
                         sinf(x * 0.015f) * sinf(z * 0.015f) * 2.0f;
            float block_y = height + noise;

            if (block_y < player_y - 30.0f) {
                continue;
            }

            float grass_color_intensity = 0.2f + noise * 0.05f;
            glColor3f(0.2f + grass_color_intensity, 0.5f + grass_color_intensity, 0.2f + grass_color_intensity);

            glBegin(GL_QUADS);
            glVertex3f(static_cast<float>(x), block_y, static_cast<float>(z));
            glVertex3f(static_cast<float>(x) + block_size, block_y, static_cast<float>(z));
            glVertex3f(static_cast<float>(x) + block_size, block_y, static_cast<float>(z) + block_size);
            glVertex3f(static_cast<float>(x), block_y, static_cast<float>(z) + block_size);
            glEnd();
        }
    }

    glEnable(GL_LIGHTING);
}

void render_projectiles(ProjectileData* projectiles, int count) {
    glDisable(GL_LIGHTING);

    for (int i = 0; i < count; i++) {
        ProjectileData& proj = projectiles[i];

        glPushMatrix();
        glTranslatef(proj.x, proj.y, proj.z);

        if (proj.type == 0) {
            glColor3f(0.6f, 0.4f, 0.2f);
            glBegin(GL_LINES);
            glVertex3f(0.0f, 0.0f, 0.0f);
            glVertex3f(0.0f, 0.5f, 0.0f);
            glEnd();

            glColor3f(0.9f, 0.9f, 0.9f);
            glBegin(GL_LINES);
            glVertex3f(0.0f, 0.5f, 0.0f);
            glVertex3f(0.0f, 0.8f, 0.0f);
            glEnd();
        }
        else if (proj.type == 1) {
            glColor3f(0.5f, 0.5f, 0.5f);
            glBegin(GL_LINES);
            glVertex3f(0.0f, 0.0f, 0.0f);
            glVertex3f(0.0f, 0.6f, 0.0f);
            glEnd();

            glColor3f(0.3f, 0.3f, 0.3f);
            glBegin(GL_LINES);
            glVertex3f(-0.1f, 0.1f, 0.0f);
            glVertex3f(0.1f, 0.1f, 0.0f);
            glEnd();
        }
        else if (proj.type == 2) {
            glColor3f(0.3f, 0.5f, 0.8f);
            glBegin(GL_LINES);
            glVertex3f(0.0f, 0.0f, 0.0f);
            glVertex3f(0.0f, 1.0f, 0.0f);
            glEnd();

            glColor3f(0.2f, 0.4f, 0.7f);
            glBegin(GL_LINES);
            glVertex3f(-0.15f, 0.2f, 0.0f);
            glVertex3f(0.0f, 0.5f, 0.0f);
            glEnd();
            glBegin(GL_LINES);
            glVertex3f(0.15f, 0.2f, 0.0f);
            glVertex3f(0.0f, 0.5f, 0.0f);
            glEnd();
        }

        glPopMatrix();
    }

    glEnable(GL_LIGHTING);
}

void render_pickups(PickupData* pickups, int count) {
    glDisable(GL_LIGHTING);

    for (int i = 0; i < count; i++) {
        PickupData& pickup = pickups[i];

        float bob_y = sinf(pickup.bob_offset) * 0.15f + 0.3f;

        glColor4f(pickup.r, pickup.g, pickup.b, pickup.a);

        glPushMatrix();
        glTranslatef(pickup.x, bob_y, pickup.z);
        glRotatef(pickup.rotation * 180.0f / 3.14159265359f, 0.0f, 1.0f, 0.0f);

        float size = 0.35f;
        glBegin(GL_QUADS);

        glVertex3f(-size, -size, -size);
        glVertex3f(size, -size, -size);
        glVertex3f(size, size, -size);
        glVertex3f(-size, size, -size);

        glVertex3f(size, -size, -size);
        glVertex3f(size, -size, size);
        glVertex3f(size, size, size);
        glVertex3f(size, size, -size);

        glVertex3f(size, -size, size);
        glVertex3f(-size, -size, size);
        glVertex3f(-size, size, size);
        glVertex3f(size, size, size);

        glVertex3f(-size, -size, size);
        glVertex3f(-size, -size, -size);
        glVertex3f(-size, size, -size);
        glVertex3f(-size, size, size);

        glVertex3f(-size, size, -size);
        glVertex3f(size, size, -size);
        glVertex3f(size, size, size);
        glVertex3f(-size, size, size);

        glVertex3f(-size, -size, size);
        glVertex3f(size, -size, size);
        glVertex3f(size, -size, -size);
        glVertex3f(-size, -size, -size);

        glEnd();

        glPopMatrix();
    }

    glEnable(GL_LIGHTING);
}

void render_tech_block(const TechBlockData* block) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(block->x, 0.5f, block->z);
    glRotatef(block->rotation * 180.0f / 3.14159265359f, 0.0f, 1.0f, 0.0f);

    if (block->a > 0.0f) {
        glColor4f(block->r, block->g, block->b, block->a);
    } else {
        glColor3f(block->r, block->g, block->b);
    }

    float block_size_half = 2.5f;

    glBegin(GL_QUADS);

    glVertex3f(-block_size_half, 0.0f, -block_size_half);
    glVertex3f(block_size_half, 0.0f, -block_size_half);
    glVertex3f(block_size_half, 0.0f, block_size_half);
    glVertex3f(-block_size_half, 0.0f, block_size_half);

    glVertex3f(-block_size_half, -block_size_half, -block_size_half);
    glVertex3f(block_size_half, -block_size_half, -block_size_half);
    glVertex3f(block_size_half, -block_size_half, block_size_half);
    glVertex3f(-block_size_half, -block_size_half, block_size_half);

    glVertex3f(-block_size_half, 0.0f, block_size_half);
    glVertex3f(block_size_half, 0.0f, block_size_half);
    glVertex3f(block_size_half, -block_size_half, block_size_half);
    glVertex3f(-block_size_half, -block_size_half, block_size_half);

    glVertex3f(-block_size_half, 0.0f, -block_size_half);
    glVertex3f(block_size_half, 0.0f, -block_size_half);
    glVertex3f(block_size_half, -block_size_half, -block_size_half);
    glVertex3f(-block_size_half, -block_size_half, -block_size_half);

    glVertex3f(-block_size_half, 0.0f, -block_size_half);
    glVertex3f(-block_size_half, 0.0f, block_size_half);
    glVertex3f(-block_size_half, -block_size_half, block_size_half);
    glVertex3f(-block_size_half, -block_size_half, -block_size_half);

    glVertex3f(block_size_half, 0.0f, -block_size_half);
    glVertex3f(block_size_half, 0.0f, block_size_half);
    glVertex3f(block_size_half, -block_size_half, block_size_half);
    glVertex3f(block_size_half, -block_size_half, -block_size_half);

    glEnd();

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_tree(const TreeData* tree) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(tree->x, 0.0f, tree->z);
    glScalef(tree->scale, tree->scale, tree->scale);

    glColor3f(0.4f, 0.26f, 0.13f);
    glBegin(GL_QUADS);
    glVertex3f(-0.3f, 0.0f, -0.3f);
    glVertex3f(0.3f, 0.0f, -0.3f);
    glVertex3f(0.3f, 2.0f, -0.3f);
    glVertex3f(-0.3f, 2.0f, -0.3f);

    glVertex3f(-0.3f, 0.0f, 0.3f);
    glVertex3f(0.3f, 0.0f, 0.3f);
    glVertex3f(0.3f, 2.0f, 0.3f);
    glVertex3f(-0.3f, 2.0f, 0.3f);

    glVertex3f(-0.3f, 0.0f, -0.3f);
    glVertex3f(-0.3f, 0.0f, 0.3f);
    glVertex3f(-0.3f, 2.0f, 0.3f);
    glVertex3f(-0.3f, 2.0f, -0.3f);

    glVertex3f(0.3f, 0.0f, -0.3f);
    glVertex3f(0.3f, 0.0f, 0.3f);
    glVertex3f(0.3f, 2.0f, 0.3f);
    glVertex3f(0.3f, 2.0f, -0.3f);
    glEnd();

    glColor3f(0.2f, 0.6f, 0.2f);

    glPushMatrix();
    glTranslatef(0.0f, 2.5f, 0.0f);

    float leaf_radius = 1.5f;
    int stacks = 8;
    int slices = 8;

    for (int i = 0; i < stacks; i++) {
        float phi1 = 3.14159265359f * i / stacks;
        float phi2 = 3.14159265359f * (i + 1) / stacks;

        for (int j = 0; j < slices; j++) {
            float theta1 = 2.0f * 3.14159265359f * j / slices;
            float theta2 = 2.0f * 3.14159265359f * (j + 1) / slices;

            float x1 = leaf_radius * sinf(phi1) * cosf(theta1);
            float y1 = leaf_radius * cosf(phi1);
            float z1 = leaf_radius * sinf(phi1) * sinf(theta1);

            float x2 = leaf_radius * sinf(phi1) * cosf(theta2);
            float y2 = leaf_radius * cosf(phi1);
            float z2 = leaf_radius * sinf(phi1) * sinf(theta2);

            float x3 = leaf_radius * sinf(phi2) * cosf(theta2);
            float y3 = leaf_radius * cosf(phi2);
            float z3 = leaf_radius * sinf(phi2) * sinf(theta2);

            float x4 = leaf_radius * sinf(phi2) * cosf(theta1);
            float y4 = leaf_radius * cosf(phi2);
            float z4 = leaf_radius * sinf(phi2) * sinf(theta1);

            glBegin(GL_QUADS);
            glVertex3f(x1, y1, z1);
            glVertex3f(x2, y2, z2);
            glVertex3f(x3, y3, z3);
            glVertex3f(x4, y4, z4);
            glEnd();
        }
    }

    glPopMatrix();
    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_trees(TreeData* trees, int count) {
    for (int i = 0; i < count; i++) {
        render_tree(&trees[i]);
    }
}

void render_large_structure(const StructureData* structure) {
    glDisable(GL_LIGHTING);

    glColor3f(structure->r, structure->g, structure->b);

    glPushMatrix();
    glTranslatef(structure->x, 0.0f, structure->z);

    glBegin(GL_QUADS);
    glVertex3f(-structure->size, 0.0f, -structure->size);
    glVertex3f(structure->size, 0.0f, -structure->size);
    glVertex3f(structure->size, 0.0f, structure->size);
    glVertex3f(-structure->size, 0.0f, structure->size);
    glEnd();

    float pillar_width = structure->size * 0.15f;

    glColor3f(structure->r * 0.8f, structure->g * 0.8f, structure->b * 0.8f);

    glPushMatrix();
    glTranslatef(-structure->size + pillar_width, 0.0f, -structure->size + pillar_width);
    glBegin(GL_QUADS);
    glVertex3f(-pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, structure->height, -pillar_width);
    glVertex3f(-pillar_width, structure->height, -pillar_width);

    glVertex3f(-pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, structure->height, pillar_width);
    glVertex3f(-pillar_width, structure->height, pillar_width);

    glVertex3f(-pillar_width, 0.0f, -pillar_width);
    glVertex3f(-pillar_width, 0.0f, pillar_width);
    glVertex3f(-pillar_width, structure->height, pillar_width);
    glVertex3f(-pillar_width, structure->height, -pillar_width);

    glVertex3f(pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, structure->height, pillar_width);
    glVertex3f(pillar_width, structure->height, -pillar_width);
    glEnd();
    glPopMatrix();

    glPushMatrix();
    glTranslatef(structure->size - pillar_width, 0.0f, -structure->size + pillar_width);
    glBegin(GL_QUADS);
    glVertex3f(-pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, structure->height, -pillar_width);
    glVertex3f(-pillar_width, structure->height, -pillar_width);

    glVertex3f(-pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, structure->height, pillar_width);
    glVertex3f(-pillar_width, structure->height, pillar_width);

    glVertex3f(-pillar_width, 0.0f, -pillar_width);
    glVertex3f(-pillar_width, 0.0f, pillar_width);
    glVertex3f(-pillar_width, structure->height, pillar_width);
    glVertex3f(-pillar_width, structure->height, -pillar_width);

    glVertex3f(pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, structure->height, pillar_width);
    glVertex3f(pillar_width, structure->height, -pillar_width);
    glEnd();
    glPopMatrix();

    glPushMatrix();
    glTranslatef(-structure->size + pillar_width, 0.0f, structure->size - pillar_width);
    glBegin(GL_QUADS);
    glVertex3f(-pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, structure->height, -pillar_width);
    glVertex3f(-pillar_width, structure->height, -pillar_width);

    glVertex3f(-pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, structure->height, pillar_width);
    glVertex3f(-pillar_width, structure->height, pillar_width);

    glVertex3f(-pillar_width, 0.0f, -pillar_width);
    glVertex3f(-pillar_width, 0.0f, pillar_width);
    glVertex3f(-pillar_width, structure->height, pillar_width);
    glVertex3f(-pillar_width, structure->height, -pillar_width);

    glVertex3f(pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, structure->height, pillar_width);
    glVertex3f(pillar_width, structure->height, -pillar_width);
    glEnd();
    glPopMatrix();

    glPushMatrix();
    glTranslatef(structure->size - pillar_width, 0.0f, structure->size - pillar_width);
    glBegin(GL_QUADS);
    glVertex3f(-pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, structure->height, -pillar_width);
    glVertex3f(-pillar_width, structure->height, -pillar_width);

    glVertex3f(-pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, structure->height, pillar_width);
    glVertex3f(-pillar_width, structure->height, pillar_width);

    glVertex3f(-pillar_width, 0.0f, -pillar_width);
    glVertex3f(-pillar_width, 0.0f, pillar_width);
    glVertex3f(-pillar_width, structure->height, pillar_width);
    glVertex3f(-pillar_width, structure->height, -pillar_width);

    glVertex3f(pillar_width, 0.0f, -pillar_width);
    glVertex3f(pillar_width, 0.0f, pillar_width);
    glVertex3f(pillar_width, structure->height, pillar_width);
    glVertex3f(pillar_width, structure->height, -pillar_width);
    glEnd();
    glPopMatrix();

    glColor3f(structure->r, structure->g, structure->b);
    glBegin(GL_QUADS);
    glVertex3f(-structure->size, structure->height, -structure->size);
    glVertex3f(structure->size, structure->height, -structure->size);
    glVertex3f(structure->size, structure->height, structure->size);
    glVertex3f(-structure->size, structure->height, structure->size);
    glEnd();

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_structures(StructureData* structures, int count) {
    for (int i = 0; i < count; i++) {
        render_large_structure(&structures[i]);
    }
}

void render_location(const LocationData* location) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(location->x, location->height, location->z);

    glColor3f(location->r, location->g, location->b);

    float size = location->scale;

    glBegin(GL_QUADS);
    glVertex3f(-size, 0.0f, -size);
    glVertex3f(size, 0.0f, -size);
    glVertex3f(size, 0.0f, size);
    glVertex3f(-size, 0.0f, size);
    glEnd();

    float wall_height = 2.0f;
    glColor3f(location->r * 0.7f, location->g * 0.7f, location->b * 0.7f);

    glBegin(GL_QUADS);
    glVertex3f(-size, 0.0f, -size);
    glVertex3f(size, 0.0f, -size);
    glVertex3f(size, wall_height, -size);
    glVertex3f(-size, wall_height, -size);

    glVertex3f(-size, 0.0f, size);
    glVertex3f(size, 0.0f, size);
    glVertex3f(size, wall_height, size);
    glVertex3f(-size, wall_height, size);

    glVertex3f(-size, 0.0f, -size);
    glVertex3f(-size, 0.0f, size);
    glVertex3f(-size, wall_height, size);
    glVertex3f(-size, wall_height, -size);

    glVertex3f(size, 0.0f, -size);
    glVertex3f(size, 0.0f, size);
    glVertex3f(size, wall_height, size);
    glVertex3f(size, wall_height, -size);
    glEnd();

    if (location->owner == 1) {
        glColor3f(1.0f, 0.8f, 0.0f);
        glBegin(GL_LINE_LOOP);
        glVertex3f(-size - 0.2f, wall_height + 0.5f, -size - 0.2f);
        glVertex3f(size + 0.2f, wall_height + 0.5f, -size - 0.2f);
        glVertex3f(size + 0.2f, wall_height + 0.5f, size + 0.2f);
        glVertex3f(-size - 0.2f, wall_height + 0.5f, size + 0.2f);
        glEnd();
    }

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_locations(LocationData* locations, int count) {
    for (int i = 0; i < count; i++) {
        render_location(&locations[i]);
    }
}

void render_npc(const NPCData* npc) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(npc->x, 0.0f, npc->z);

    float bob_y = sinf(npc->animation_offset) * 0.1f;

    if (npc->selected) {
        glColor3f(1.0f, 1.0f, 0.0f);
        glBegin(GL_LINE_LOOP);
        glVertex3f(-0.8f, 2.5f + bob_y, -0.8f);
        glVertex3f(0.8f, 2.5f + bob_y, -0.8f);
        glVertex3f(0.8f, 2.5f + bob_y, 0.8f);
        glVertex3f(-0.8f, 2.5f + bob_y, 0.8f);
        glEnd();
    }

    glColor3f(npc->r, npc->g, npc->b);

    glBegin(GL_QUADS);
    glVertex3f(-0.4f, 1.5f + bob_y, -0.4f);
    glVertex3f(0.4f, 1.5f + bob_y, -0.4f);
    glVertex3f(0.4f, 2.1f + bob_y, -0.4f);
    glVertex3f(-0.4f, 2.1f + bob_y, -0.4f);

    glVertex3f(-0.4f, 1.5f + bob_y, 0.4f);
    glVertex3f(0.4f, 1.5f + bob_y, 0.4f);
    glVertex3f(0.4f, 2.1f + bob_y, 0.4f);
    glVertex3f(-0.4f, 2.1f + bob_y, 0.4f);

    glVertex3f(-0.4f, 1.5f + bob_y, -0.4f);
    glVertex3f(-0.4f, 1.5f + bob_y, 0.4f);
    glVertex3f(-0.4f, 2.1f + bob_y, 0.4f);
    glVertex3f(-0.4f, 2.1f + bob_y, -0.4f);

    glVertex3f(0.4f, 1.5f + bob_y, -0.4f);
    glVertex3f(0.4f, 1.5f + bob_y, 0.4f);
    glVertex3f(0.4f, 2.1f + bob_y, 0.4f);
    glVertex3f(0.4f, 2.1f + bob_y, -0.4f);

    glVertex3f(-0.4f, 2.1f + bob_y, -0.4f);
    glVertex3f(0.4f, 2.1f + bob_y, -0.4f);
    glVertex3f(0.4f, 2.1f + bob_y, 0.4f);
    glVertex3f(-0.4f, 2.1f + bob_y, 0.4f);
    glEnd();

    glColor3f(npc->r * 0.8f, npc->g * 0.8f, npc->b * 0.8f);
    glBegin(GL_QUADS);
    glVertex3f(-0.5f, 0.0f, -0.3f);
    glVertex3f(0.5f, 0.0f, -0.3f);
    glVertex3f(0.5f, 1.5f + bob_y, -0.3f);
    glVertex3f(-0.5f, 1.5f + bob_y, -0.3f);

    glVertex3f(-0.5f, 0.0f, 0.3f);
    glVertex3f(0.5f, 0.0f, 0.3f);
    glVertex3f(0.5f, 1.5f + bob_y, 0.3f);
    glVertex3f(-0.5f, 1.5f + bob_y, 0.3f);

    glVertex3f(-0.5f, 0.0f, -0.3f);
    glVertex3f(-0.5f, 0.0f, 0.3f);
    glVertex3f(-0.5f, 1.5f + bob_y, 0.3f);
    glVertex3f(-0.5f, 1.5f + bob_y, -0.3f);

    glVertex3f(0.5f, 0.0f, -0.3f);
    glVertex3f(0.5f, 0.0f, 0.3f);
    glVertex3f(0.5f, 1.5f + bob_y, 0.3f);
    glVertex3f(0.5f, 1.5f + bob_y, -0.3f);
    glEnd();

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_npcs(NPCData* npcs, int count) {
    for (int i = 0; i < count; i++) {
        render_npc(&npcs[i]);
    }
}

void render_enemy(const EnemyData* enemy) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(enemy->x, 0.0f, enemy->z);

    glColor3f(enemy->r, enemy->g, enemy->b);

    glBegin(GL_QUADS);
    glVertex3f(-0.4f, 1.2f, -0.4f);
    glVertex3f(0.4f, 1.2f, -0.4f);
    glVertex3f(0.4f, 1.8f, -0.4f);
    glVertex3f(-0.4f, 1.8f, -0.4f);

    glVertex3f(-0.4f, 1.2f, 0.4f);
    glVertex3f(0.4f, 1.2f, 0.4f);
    glVertex3f(0.4f, 1.8f, 0.4f);
    glVertex3f(-0.4f, 1.8f, 0.4f);

    glVertex3f(-0.4f, 1.2f, -0.4f);
    glVertex3f(-0.4f, 1.2f, 0.4f);
    glVertex3f(-0.4f, 1.8f, 0.4f);
    glVertex3f(-0.4f, 1.8f, -0.4f);

    glVertex3f(0.4f, 1.2f, -0.4f);
    glVertex3f(0.4f, 1.2f, 0.4f);
    glVertex3f(0.4f, 1.8f, 0.4f);
    glVertex3f(0.4f, 1.8f, -0.4f);
    glEnd();

    glColor3f(enemy->r * 0.7f, enemy->g * 0.7f, enemy->b * 0.7f);
    glBegin(GL_QUADS);
    glVertex3f(-0.5f, 0.0f, -0.3f);
    glVertex3f(0.5f, 0.0f, -0.3f);
    glVertex3f(0.5f, 1.2f, -0.3f);
    glVertex3f(-0.5f, 1.2f, -0.3f);

    glVertex3f(-0.5f, 0.0f, 0.3f);
    glVertex3f(0.5f, 0.0f, 0.3f);
    glVertex3f(0.5f, 1.2f, 0.3f);
    glVertex3f(-0.5f, 1.2f, 0.3f);
    glEnd();

    float health_ratio = enemy->health / enemy->max_health;
    glColor3f(1.0f - health_ratio, health_ratio, 0.0f);
    glBegin(GL_QUADS);
    glVertex3f(-0.6f, 2.0f, -0.3f);
    glVertex3f(-0.6f + health_ratio * 1.2f, 2.0f, -0.3f);
    glVertex3f(-0.6f + health_ratio * 1.2f, 2.1f, -0.3f);
    glVertex3f(-0.6f, 2.1f, -0.3f);
    glEnd();

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_enemies(EnemyData* enemies, int count) {
    for (int i = 0; i < count; i++) {
        render_enemy(&enemies[i]);
    }
}

void render_general(const GeneralData* general) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(general->x, 0.0f, general->z);

    float bob_y = sinf(general->animation_offset) * 0.08f;

    glColor3f(general->r, general->g, general->b);

    glBegin(GL_QUADS);
    glVertex3f(-0.5f, 1.6f + bob_y, -0.5f);
    glVertex3f(0.5f, 1.6f + bob_y, -0.5f);
    glVertex3f(0.5f, 2.3f + bob_y, -0.5f);
    glVertex3f(-0.5f, 2.3f + bob_y, -0.5f);

    glVertex3f(-0.5f, 1.6f + bob_y, 0.5f);
    glVertex3f(0.5f, 1.6f + bob_y, 0.5f);
    glVertex3f(0.5f, 2.3f + bob_y, 0.5f);
    glVertex3f(-0.5f, 2.3f + bob_y, 0.5f);
    glEnd();

    glColor3f(general->r * 0.75f, general->g * 0.75f, general->b * 0.75f);
    glBegin(GL_QUADS);
    glVertex3f(-0.6f, 0.0f, -0.4f);
    glVertex3f(0.6f, 0.0f, -0.4f);
    glVertex3f(0.6f, 1.6f + bob_y, -0.4f);
    glVertex3f(-0.6f, 1.6f + bob_y, -0.4f);

    glVertex3f(-0.6f, 0.0f, 0.4f);
    glVertex3f(0.6f, 0.0f, 0.4f);
    glVertex3f(0.6f, 1.6f + bob_y, 0.4f);
    glVertex3f(-0.6f, 1.6f + bob_y, 0.4f);
    glEnd();

    if (general->has_weapon) {
        glColor3f(0.7f, 0.7f, 0.7f);
        glBegin(GL_LINES);
        glVertex3f(0.4f, 1.0f + bob_y, 0.0f);
        glVertex3f(1.0f, 0.8f + bob_y, 0.0f);
        glEnd();
    }

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_generals(GeneralData* generals, int count) {
    for (int i = 0; i < count; i++) {
        render_general(&generals[i]);
    }
}

void render_pet(const PetData* pet) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(pet->x, 0.0f, pet->z);

    float bob_y = sinf(pet->animation_offset) * 0.05f;

    glColor3f(pet->r, pet->g, pet->b);

    glBegin(GL_QUADS);
    glVertex3f(-0.3f, 0.5f + bob_y, -0.3f);
    glVertex3f(0.3f, 0.5f + bob_y, -0.3f);
    glVertex3f(0.3f, 0.9f + bob_y, -0.3f);
    glVertex3f(-0.3f, 0.9f + bob_y, -0.3f);

    glVertex3f(-0.3f, 0.5f + bob_y, 0.3f);
    glVertex3f(0.3f, 0.5f + bob_y, 0.3f);
    glVertex3f(0.3f, 0.9f + bob_y, 0.3f);
    glVertex3f(-0.3f, 0.9f + bob_y, 0.3f);
    glEnd();

    glColor3f(pet->r * 0.9f, pet->g * 0.9f, pet->b * 0.9f);
    glBegin(GL_QUADS);
    glVertex3f(-0.4f, 0.0f, -0.25f);
    glVertex3f(0.4f, 0.0f, -0.25f);
    glVertex3f(0.4f, 0.5f + bob_y, -0.25f);
    glVertex3f(-0.4f, 0.5f + bob_y, -0.25f);

    glVertex3f(-0.4f, 0.0f, 0.25f);
    glVertex3f(0.4f, 0.0f, 0.25f);
    glVertex3f(0.4f, 0.5f + bob_y, 0.25f);
    glVertex3f(-0.4f, 0.5f + bob_y, 0.25f);
    glEnd();

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_pets(PetData* pets, int count) {
    for (int i = 0; i < count; i++) {
        render_pet(&pets[i]);
    }
}

void render_player(const PlayerData* player) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(player->x, player->y, player->z);
    glRotatef(player->yaw, 0.0f, 1.0f, 0.0f);

    glColor3f(player->r, player->g, player->b);

    glBegin(GL_QUADS);
    glVertex3f(-0.4f, 1.5f, -0.4f);
    glVertex3f(0.4f, 1.5f, -0.4f);
    glVertex3f(0.4f, 2.1f, -0.4f);
    glVertex3f(-0.4f, 2.1f, -0.4f);

    glVertex3f(-0.4f, 1.5f, 0.4f);
    glVertex3f(0.4f, 1.5f, 0.4f);
    glVertex3f(0.4f, 2.1f, 0.4f);
    glVertex3f(-0.4f, 2.1f, 0.4f);
    glEnd();

    glColor3f(player->r * 0.8f, player->g * 0.8f, player->b * 0.8f);
    glBegin(GL_QUADS);
    glVertex3f(-0.5f, 0.0f, -0.3f);
    glVertex3f(0.5f, 0.0f, -0.3f);
    glVertex3f(0.5f, 1.5f, -0.3f);
    glVertex3f(-0.5f, 1.5f, -0.3f);

    glVertex3f(-0.5f, 0.0f, 0.3f);
    glVertex3f(0.5f, 0.0f, 0.3f);
    glVertex3f(0.5f, 1.5f, 0.3f);
    glVertex3f(-0.5f, 1.5f, 0.3f);
    glEnd();

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_follower(const FollowerData* follower) {
    glDisable(GL_LIGHTING);

    glPushMatrix();
    glTranslatef(follower->x, 0.0f, follower->z);

    float bob_y = sinf(follower->animation_offset) * 0.08f;

    glColor3f(follower->r, follower->g, follower->b);

    glBegin(GL_QUADS);
    glVertex3f(-0.35f, 1.4f + bob_y, -0.35f);
    glVertex3f(0.35f, 1.4f + bob_y, -0.35f);
    glVertex3f(0.35f, 2.0f + bob_y, -0.35f);
    glVertex3f(-0.35f, 2.0f + bob_y, -0.35f);

    glVertex3f(-0.35f, 1.4f + bob_y, 0.35f);
    glVertex3f(0.35f, 1.4f + bob_y, 0.35f);
    glVertex3f(0.35f, 2.0f + bob_y, 0.35f);
    glVertex3f(-0.35f, 2.0f + bob_y, 0.35f);
    glEnd();

    glColor3f(follower->r * 0.8f, follower->g * 0.8f, follower->b * 0.8f);
    glBegin(GL_QUADS);
    glVertex3f(-0.45f, 0.0f, -0.28f);
    glVertex3f(0.45f, 0.0f, -0.28f);
    glVertex3f(0.45f, 1.4f + bob_y, -0.28f);
    glVertex3f(-0.45f, 1.4f + bob_y, -0.28f);

    glVertex3f(-0.45f, 0.0f, 0.28f);
    glVertex3f(0.45f, 0.0f, 0.28f);
    glVertex3f(0.45f, 1.4f + bob_y, 0.28f);
    glVertex3f(-0.45f, 1.4f + bob_y, 0.28f);
    glEnd();

    glPopMatrix();
    glEnable(GL_LIGHTING);
}

void render_followers(FollowerData* followers, int count) {
    for (int i = 0; i < count; i++) {
        render_follower(&followers[i]);
    }
}

void render_particles(Vec3f* positions, Color4f* colors, int count) {
    glDisable(GL_LIGHTING);
    glPointSize(3.0f);

    glBegin(GL_POINTS);
    for (int i = 0; i < count; i++) {
        glColor4f(colors[i].r, colors[i].g, colors[i].b, colors[i].a);
        glVertex3f(positions[i].x, positions[i].y, positions[i].z);
    }
    glEnd();

    glEnable(GL_LIGHTING);
}